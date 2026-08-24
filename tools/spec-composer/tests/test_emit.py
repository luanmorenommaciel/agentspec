"""Tests for the emit boundary: promotion, provenance, and gate-equivalent rebuilds."""

from __future__ import annotations

import json
import os
import shutil
from collections import Counter
from pathlib import Path

import pytest
from _helpers import judge_less_document

from spec_composer import engine
from spec_composer.contract import PipelineSpec
from spec_composer.emit import EmitError, archive_spec, promote, resolve_archive_dir
from spec_composer.engine import compose
from spec_composer.models import ComposeRequest, ComposeResult, Disposition, StageVerdict
from spec_composer.runstate import RunLog, run_dir, slug


def _nth_body(body: str, occurrence: int) -> str:
    """The first presentation is the scripted body verbatim; a repeat presentation
    must differ, or the conductor reports it as stale rather than accepting it."""
    return body if occurrence == 1 else f"{body}\n<!-- revision {occurrence} -->\n"


def _write(result: ComposeResult, body: str) -> None:
    assert result.expected_path is not None
    result.expected_path.parent.mkdir(parents=True, exist_ok=True)
    result.expected_path.write_text(body, encoding="utf-8")


def _drive(
    pipeline: PipelineSpec,
    request: ComposeRequest,
    content: dict[str, str],
    *,
    limit: int = 12,
) -> ComposeResult:
    """Answer every `waiting` disposition with the scripted body for that stage.

    A stage asked a second time is answered with a DISTINCT body: the conductor
    rejects a re-presented artifact as stale, so a repair loop only advances when
    the host produces something the gate has not already seen."""
    answered: Counter[str] = Counter()
    result = compose(request, pipeline)
    for _ in range(limit):
        if result.disposition is not Disposition.WAITING:
            return result
        assert result.stage is not None
        answered[result.stage] += 1
        _write(result, _nth_body(content[result.stage], answered[result.stage]))
        result = compose(request, pipeline)
    raise AssertionError(f"the run did not settle within {limit} handoffs")


def _verdict_signature(trail: tuple[StageVerdict, ...]) -> list[tuple[str, str, tuple[str, ...]]]:
    return [
        (item.stage, item.verdict.level.name, tuple(sorted(f.rule for f in item.verdict.findings)))
        for item in trail
    ]


def test_emit_target_absent_after_gate_b_fail(
    spec_text: str, rejected_agent_text: str, target: Path
) -> None:
    """An artifact that never clears Gate B is never promoted."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    content = {"create-spec": spec_text, "generate-agent": rejected_agent_text}
    result = _drive(pipeline, request, content)

    assert result.disposition is Disposition.BLOCKED
    assert not target.exists()


def test_no_partial_artifact_at_target(
    spec_text: str, rejected_agent_text: str, target: Path
) -> None:
    """A target that already existed before a failing run is left byte-identical
    to its pre-run state, and no temporary promotion artifact is left behind."""
    target.parent.mkdir(parents=True, exist_ok=True)
    placeholder = b"pre-existing agent content"
    target.write_bytes(placeholder)

    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    content = {"create-spec": spec_text, "generate-agent": rejected_agent_text}
    result = _drive(pipeline, request, content)

    assert result.disposition is Disposition.BLOCKED
    assert target.read_bytes() == placeholder
    assert list(target.parent.glob(f"{target.name}.tmp-*")) == []


def test_staged_copy_remains_after_gate_fail(
    spec_text: str, rejected_agent_text: str, target: Path
) -> None:
    """The rejected staged artifact is left on disk for inspection rather than
    being cleaned up when the run routes back for a repair attempt."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)

    result = compose(request, pipeline)
    _write(result, spec_text)

    result = compose(request, pipeline)
    assert result.stage == "generate-agent"
    staged_path = result.expected_path
    assert staged_path is not None
    _write(result, rejected_agent_text)

    result = compose(request, pipeline)
    assert result.disposition is Disposition.WAITING
    assert result.expected_path != staged_path
    assert staged_path.is_file()
    assert staged_path.read_text(encoding="utf-8") == rejected_agent_text


def test_rebuild_from_archived_spec_is_gate_equivalent(
    spec_text: str, agent_text: str, target: Path, tmp_path: Path
) -> None:
    """Rebuilding from the archived spec reaches the same gate verdicts at the
    same tier, even though the run directory and target are entirely new."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    result = _drive(pipeline, request, {"create-spec": spec_text, "generate-agent": agent_text})
    assert result.disposition is Disposition.EMITTED

    archive_dir = resolve_archive_dir(request.name, pipeline.archive)
    archived_spec = archive_dir / f"{slug(request.name)}.spec.md"
    assert archived_spec.read_text(encoding="utf-8") == spec_text

    rebuilt_target = tmp_path / "rebuild" / "code-reviewer.md"
    rebuild_request = ComposeRequest(
        name=request.name, target=rebuilt_target, spec_path=archived_spec
    )
    rebuilt = _drive(pipeline, rebuild_request, {"generate-agent": agent_text})

    assert rebuilt.disposition is Disposition.EMITTED
    assert _verdict_signature(result.trail) == _verdict_signature(rebuilt.trail)


def test_archive_written_and_never_read(spec_text: str, agent_text: str, target: Path) -> None:
    """The archive holds the spec verbatim plus provenance, and is never read
    back — deleting it changes nothing about how the run behaves."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    result = _drive(pipeline, request, {"create-spec": spec_text, "generate-agent": agent_text})
    assert result.disposition is Disposition.EMITTED

    archive_dir = resolve_archive_dir(request.name, pipeline.archive)
    archived_spec = archive_dir / f"{slug(request.name)}.spec.md"
    assert archived_spec.read_text(encoding="utf-8") == spec_text
    assert (archive_dir / "provenance.json").is_file()

    shutil.rmtree(archive_dir)
    resumed = compose(request, pipeline)

    assert resumed.disposition is Disposition.EMITTED
    assert not archive_dir.exists()


def test_provenance_records_resolved_target(spec_text: str, agent_text: str, target: Path) -> None:
    """Provenance carries the pipeline identity, the epoch and spend accounting,
    the per-stage stamp digests, and the fully resolved emit target."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    result = _drive(pipeline, request, {"create-spec": spec_text, "generate-agent": agent_text})
    assert result.disposition is Disposition.EMITTED

    archive_dir = resolve_archive_dir(request.name, pipeline.archive)
    provenance = json.loads((archive_dir / "provenance.json").read_text(encoding="utf-8"))

    assert provenance["pipeline"] == pipeline.pipeline
    assert provenance["version"] == pipeline.version
    assert provenance["epoch"] == result.epoch
    assert provenance["attempts_spent"] == result.attempts_spent
    assert provenance["target"] == str(target.expanduser().resolve())

    stamped_stages = {stage["stage"] for stage in provenance["stamps"]}
    assert stamped_stages == {stage.id for stage in pipeline.stages}


def test_archive_failure_keeps_emitted(
    monkeypatch: pytest.MonkeyPatch, spec_text: str, agent_text: str, target: Path
) -> None:
    """A promotion that succeeds but whose archive write fails afterward still
    reports emitted success; the archive failure is recorded, not swallowed."""

    def _raise(*args: object, **kwargs: object) -> Path:
        raise OSError("archive destination unwritable")

    monkeypatch.setattr(engine, "archive_spec", _raise)

    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    result = _drive(pipeline, request, {"create-spec": spec_text, "generate-agent": agent_text})

    assert result.disposition is Disposition.EMITTED
    assert target.read_text(encoding="utf-8") == agent_text

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    failures = [row for row in records if row.kind == "event" and row.reason == "archive-failed"]
    assert len(failures) == 1


def test_archive_template_must_be_relative_and_inside_workspace(target: Path) -> None:
    """A bad archive template is rejected before any stage runs, so it can
    never leave a promoted artifact with no provenance behind it."""
    with pytest.raises(EmitError):
        resolve_archive_dir("code-reviewer", "/absolute/archive/{name}/")
    with pytest.raises(EmitError):
        resolve_archive_dir("code-reviewer", "../outside/{name}/")

    document = judge_less_document()
    document["archive"] = "/absolute/archive/{name}/"
    pipeline = PipelineSpec.from_mapping(document)
    request = ComposeRequest(name="code-reviewer", target=target)

    with pytest.raises(EmitError):
        compose(request, pipeline)

    assert not target.exists()
    assert not run_dir(pipeline.pipeline, target).exists()


def test_promote_raises_when_nothing_staged(tmp_path: Path) -> None:
    with pytest.raises(EmitError):
        promote(tmp_path / "missing.md", tmp_path / "target.md")


def test_promote_creates_target_parent_directory(tmp_path: Path) -> None:
    staged = tmp_path / "staged.md"
    staged.write_bytes(b"staged content")
    target = tmp_path / "nested" / "deep" / "target.md"

    promote(staged, target)

    assert target.parent.is_dir()
    assert target.read_bytes() == b"staged content"


def test_promote_target_matches_staged_bytes(tmp_path: Path) -> None:
    staged = tmp_path / "staged.md"
    staged.write_bytes(b"identical bytes")
    target = tmp_path / "target.md"

    promote(staged, target)

    assert target.read_bytes() == staged.read_bytes()


def test_promote_leaves_no_temporary_file(tmp_path: Path) -> None:
    staged = tmp_path / "staged.md"
    staged.write_bytes(b"content")
    target = tmp_path / "target.md"

    promote(staged, target)

    assert list(target.parent.glob(f"{target.name}.tmp-*")) == []


def test_hand_edited_target_pauses_instead_of_being_overwritten(
    spec_text: str, agent_text: str, target: Path
) -> None:
    """After emission the artifact's own frontmatter is the canonical spec, so a
    target edited in place is somebody's work, not the conductor's staging. No
    stamp accounts for those bytes and they are not the staged bytes either, so
    the run pauses and writes nothing."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    result = _drive(pipeline, request, {"create-spec": spec_text, "generate-agent": agent_text})
    assert result.disposition is Disposition.EMITTED

    edited = f"{agent_text}\n<!-- tightened by hand -->\n"
    target.write_text(edited, encoding="utf-8")

    paused = compose(request, pipeline)
    assert paused.disposition is Disposition.PAUSED
    assert paused.reason == "target-modified"
    assert target.read_text(encoding="utf-8") == edited

    kept = target.with_suffix(".md.kept")
    target.rename(kept)
    resumed = compose(request, pipeline)
    assert resumed.disposition is Disposition.EMITTED
    assert target.read_text(encoding="utf-8") == agent_text
    assert kept.read_text(encoding="utf-8") == edited


def test_unrelated_pre_existing_target_is_never_promoted_over(
    spec_text: str, agent_text: str, target: Path
) -> None:
    """The guard does not need a previous emit to protect a file: a target that
    was never this pipeline's output is left exactly as it was."""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"an artifact from somewhere else")

    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    result = _drive(pipeline, request, {"create-spec": spec_text, "generate-agent": agent_text})

    assert result.disposition is Disposition.PAUSED
    assert result.reason == "target-modified"
    assert target.read_bytes() == b"an artifact from somewhere else"


def test_archive_collision_is_refused_rather_than_overwritten(tmp_path: Path) -> None:
    """The archive is keyed by artifact NAME, so two artifacts sharing a name
    would land in one directory. Replacing one build record with another's would
    destroy provenance, so the second write is refused."""
    destination = tmp_path / "archive" / "code-reviewer"
    spec = tmp_path / "code-reviewer.spec.md"
    spec.write_text("---\nname: code-reviewer\n---\n", encoding="utf-8")

    archive_spec(destination, spec, {"target": str(tmp_path / "one" / "code-reviewer.md")})
    archive_spec(destination, spec, {"target": str(tmp_path / "one" / "code-reviewer.md")})
    with pytest.raises(EmitError):
        archive_spec(destination, spec, {"target": str(tmp_path / "two" / "code-reviewer.md")})


def test_archive_collision_keeps_emitted_and_records_the_failure(
    spec_text: str, agent_text: str, target: Path, tmp_path: Path
) -> None:
    """A collision is an archive failure, and an archive failure never restates
    what happened to the artifact: the second target is emitted, the first
    artifact's provenance survives untouched, and the run log carries the event."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    content = {"create-spec": spec_text, "generate-agent": agent_text}

    first = ComposeRequest(name="code-reviewer", target=target)
    assert _drive(pipeline, first, content).disposition is Disposition.EMITTED

    other = tmp_path / "elsewhere" / "code-reviewer.md"
    second = ComposeRequest(name="code-reviewer", target=other)
    rebuilt = _drive(pipeline, second, content)

    assert rebuilt.disposition is Disposition.EMITTED
    assert other.read_text(encoding="utf-8") == agent_text

    records = RunLog(run_dir(pipeline.pipeline, other) / "run.jsonl").records()
    failures = [row for row in records if row.kind == "event" and row.reason == "archive-failed"]
    assert len(failures) == 1

    archive_dir = resolve_archive_dir(second.name, pipeline.archive)
    provenance = json.loads((archive_dir / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["target"] == str(target.expanduser().resolve())


def test_promotion_failure_is_an_error_that_leaves_the_target_absent(
    spec_text: str, agent_text: str, target: Path
) -> None:
    """Promotion fails closed. When the target's directory cannot be written, the
    run reports the operational failure and no partial artifact appears."""
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("a read-only directory does not stop a superuser write")

    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)

    result = compose(request, pipeline)
    _write(result, spec_text)
    result = compose(request, pipeline)
    assert result.stage == "generate-agent"
    _write(result, agent_text)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.parent.chmod(0o555)
    try:
        failed = compose(request, pipeline)
    finally:
        target.parent.chmod(0o755)

    assert failed.disposition is Disposition.ERROR
    assert failed.reason == "promotion-failed"
    assert not target.exists()
    assert list(target.parent.glob(f"{target.name}.tmp-*")) == []

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    events = [row for row in records if row.kind == "event" and row.reason == "promotion-failed"]
    assert events
