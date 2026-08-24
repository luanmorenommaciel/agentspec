"""Resume-safety tests for the conductor's pending, skip, and freshness rules."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from _helpers import REJECTED_AGENT_TEXT, SPEC_TEXT, judge_less_document
from spec_judge.evaluator import Concern, EvalRequest, EvalResult, FakeEvaluator
from spec_linter import Level

from spec_composer.contract import PipelineSpec
from spec_composer.engine import compose
from spec_composer.generator import FakeGenerator
from spec_composer.models import (
    ComposeRequest,
    ComposeResult,
    Disposition,
    GenerationRequest,
)
from spec_composer.runstate import RunLog, run_dir


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
    evaluator: FakeEvaluator | None = None,
    limit: int = 12,
) -> ComposeResult:
    """Answer every `waiting` disposition with the scripted body for that stage.

    A stage asked a second time is answered with a DISTINCT body: the conductor
    rejects a re-presented artifact as stale, so a repair loop only advances when
    the host produces something the gate has not already seen."""
    answered: Counter[str] = Counter()
    result = compose(request, pipeline, evaluator=evaluator)
    for _ in range(limit):
        if result.disposition is not Disposition.WAITING:
            return result
        assert result.stage is not None
        answered[result.stage] += 1
        _write(result, _nth_body(content[result.stage], answered[result.stage]))
        result = compose(request, pipeline, evaluator=evaluator)
    raise AssertionError(f"the run did not settle within {limit} handoffs")


def _mutated_spec(text: str) -> str:
    return text.replace(
        "Review Python diffs against the house standards and report structured findings",
        "Review Python diffs against the house standards and report structured findings.",
    )


def test_stamp_skips_only_on_matching_hash(spec_text: str, agent_text: str, target: Path) -> None:
    """A resumed run that changed nothing on disk re-derives every stamp as a
    match and dispatches no stage a second time."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    result = _drive(pipeline, request, {"create-spec": spec_text, "generate-agent": agent_text})
    assert result.disposition is Disposition.EMITTED

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    stamp_count = sum(1 for row in records if row.kind == "stamp")

    resumed = compose(request, pipeline)
    assert resumed.disposition is Disposition.EMITTED

    records_after = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    assert sum(1 for row in records_after if row.kind == "stamp") == stamp_count
    assert sum(1 for row in records_after if row.kind == "run-closed") == 2


def test_mutated_spec_invalidates_gate_a_stamp(spec_text: str, target: Path) -> None:
    """Editing the spec after Gate A passed but before generation ran re-runs
    Gate A on the new content and leaves generation waiting on its own evidence,
    never on the stale Gate A stamp."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)

    result = compose(request, pipeline)
    spec_path = result.expected_path
    assert spec_path is not None
    _write(result, spec_text)

    result = compose(request, pipeline)
    assert result.disposition is Disposition.WAITING
    assert result.stage == "generate-agent"

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    first_gate_a = next(row for row in records if row.kind == "stamp" and row.stage == "gate-a")

    mutated = _mutated_spec(spec_text)
    assert mutated != spec_text
    spec_path.write_text(mutated, encoding="utf-8")

    result = compose(request, pipeline)
    assert result.disposition is Disposition.WAITING
    assert result.stage == "generate-agent"
    assert result.reason == "awaiting-artifact"

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    gate_a_stamps = [row for row in records if row.kind == "stamp" and row.stage == "gate-a"]
    assert len(gate_a_stamps) == 2
    assert gate_a_stamps[1].input_hash != first_gate_a.input_hash
    assert gate_a_stamps[1].verdict == Level.PASS.name
    assert [row for row in records if row.kind == "stamp" and row.stage == "generate-agent"] == []


def test_spec_edit_after_gate_a_invalidates_generate_and_waits_stale(
    shipped_document: dict[str, Any], spec_text: str, agent_text: str, target: Path
) -> None:
    """Editing the spec after generation already staged an artifact this epoch
    changes generate's input hash, so the untouched staged copy reads as stale
    rather than being accepted or silently skipped."""
    pipeline = PipelineSpec.from_mapping(shipped_document)
    request = ComposeRequest(name="code-reviewer", target=target)

    result = compose(request, pipeline)
    spec_path = result.expected_path
    assert spec_path is not None
    _write(result, spec_text)

    result = compose(request, pipeline)
    assert result.stage == "generate-agent"
    _write(result, agent_text)

    result = compose(request, pipeline)
    assert result.disposition is Disposition.PAUSED
    assert result.stage == "judge-agent"
    assert result.reason == "judge-unavailable"

    spec_path.write_text(_mutated_spec(spec_text), encoding="utf-8")

    result = compose(request, pipeline)
    assert result.disposition is Disposition.WAITING
    assert result.stage == "generate-agent"
    assert result.reason == "stale-artifact"

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    generate_stamps = [
        row for row in records if row.kind == "stamp" and row.stage == "generate-agent"
    ]
    assert len(generate_stamps) == 1


def test_gate_b_failure_does_not_reopen_create_spec(
    spec_text: str, rejected_agent_text: str, agent_text: str, target: Path
) -> None:
    """A Gate B rejection routes feedback to generation only; the spec and its
    Gate A clearance are never re-demanded on the strength of a downstream
    reject the host had no part in causing."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)

    result = compose(request, pipeline)
    _write(result, spec_text)

    result = compose(request, pipeline)
    _write(result, rejected_agent_text)

    result = compose(request, pipeline)
    assert result.disposition is Disposition.WAITING
    assert result.stage == "generate-agent"
    _write(result, agent_text)

    result = compose(request, pipeline)
    assert result.disposition is Disposition.EMITTED

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    assert sum(1 for row in records if row.kind == "stamp" and row.stage == "create-spec") == 1
    assert sum(1 for row in records if row.kind == "stamp" and row.stage == "gate-a") == 1


def test_gate_a_failure_marks_create_pending_and_waits_stale(spec_text: str, target: Path) -> None:
    """A Gate A rejection marks creation pending against a fixed path; presenting
    the same rejected content again is read as stale rather than accepted."""
    rejected_spec = spec_text.replace("trigger_count: 4", "trigger_count: 1")
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)

    result = compose(request, pipeline)
    _write(result, rejected_spec)

    result = compose(request, pipeline)
    assert result.disposition is Disposition.WAITING
    assert result.stage == "create-spec"
    assert result.reason == "stale-artifact"

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    spends = [row for row in records if row.kind == "spend"]
    assert len(spends) == 1
    assert spends[0].route_to == "create-spec"
    gate_a_stamps = [row for row in records if row.kind == "stamp" and row.stage == "gate-a"]
    assert len(gate_a_stamps) == 1
    assert gate_a_stamps[0].verdict == Level.FAIL.name


def test_attempts_spent_carries_across_processes(
    spec_text: str, agent_text: str, rejected_agent_text: str, target: Path
) -> None:
    """The spent budget is folded fresh from the log on every call, so a call
    that observes no new evidence reports the same count as the call before it."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)

    result = compose(request, pipeline)
    _write(result, spec_text)

    result = compose(request, pipeline)
    _write(result, rejected_agent_text)

    result = compose(request, pipeline)
    assert result.disposition is Disposition.WAITING
    assert result.attempts_spent == 1

    result = compose(request, pipeline)
    assert result.disposition is Disposition.WAITING
    assert result.attempts_spent == 1

    _write(result, agent_text)
    result = compose(request, pipeline)
    assert result.disposition is Disposition.EMITTED
    assert result.attempts_spent == 1

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    assert sum(1 for row in records if row.kind == "spend") == 1


def test_judge_warn_stamp_skips_on_resume(
    shipped_document: dict[str, Any], spec_text: str, agent_text: str, target: Path
) -> None:
    """A WARN judge verdict is not FAIL, so a resumed run treats it as settled
    evidence and never pays for a second evaluation."""
    pipeline = PipelineSpec.from_mapping(shipped_document)
    request = ComposeRequest(name="code-reviewer", target=target)
    calls = [0]

    def script(eval_request: EvalRequest) -> EvalResult:
        calls[0] += 1
        concerns: tuple[Concern, ...] = ()
        if eval_request.role == "fault-seeker":
            concerns = (
                Concern(
                    category="B2",
                    severity="medium",
                    evidence="the report omits a declared field",
                    expected="every declared required field is present",
                    recommendation="add the missing field to the output",
                ),
            )
        return EvalResult(
            role=eval_request.role, model="fake-model", confidence=0.9, concerns=concerns
        )

    evaluator = FakeEvaluator(script)
    content = {"create-spec": spec_text, "generate-agent": agent_text}
    result = _drive(pipeline, request, content, evaluator=evaluator)

    assert result.disposition is Disposition.EMITTED
    assert calls[0] == 3

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    judge_stamps = [row for row in records if row.kind == "stamp" and row.stage == "judge-agent"]
    assert len(judge_stamps) == 1
    assert judge_stamps[0].verdict == Level.WARN.name

    resumed = compose(request, pipeline, evaluator=evaluator)
    assert resumed.disposition is Disposition.EMITTED
    assert calls[0] == 3


def test_deleted_target_repromotes(spec_text: str, agent_text: str, target: Path) -> None:
    """Deleting the emitted target does not require a new artifact — the
    still-present staged copy is enough to repromote from."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    result = _drive(pipeline, request, {"create-spec": spec_text, "generate-agent": agent_text})
    assert result.disposition is Disposition.EMITTED
    assert target.is_file()

    target.unlink()
    resumed = compose(request, pipeline)
    assert resumed.disposition is Disposition.EMITTED
    assert target.read_bytes() == agent_text.encode("utf-8")

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    assert sum(1 for row in records if row.kind == "stamp" and row.stage == "generate-agent") == 1
    assert sum(1 for row in records if row.kind == "stamp" and row.stage == "emit-agent") == 2


def test_route_to_is_recorded_in_the_evidence_log(
    spec_text: str, rejected_agent_text: str, target: Path
) -> None:
    """Every routing decision is derivable after the fact: the spend row names
    the stage it sent feedback to and the findings that drove the decision."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    content = {"create-spec": spec_text, "generate-agent": rejected_agent_text}

    result = _drive(pipeline, request, content)
    assert result.disposition is Disposition.BLOCKED

    records = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl").records()
    spends = [row for row in records if row.kind == "spend"]
    assert spends
    assert all(row.stage == "gate-b" for row in spends)
    routed, exhausted = spends[:-1], spends[-1]
    assert routed
    assert all(row.route_to == "generate-agent" for row in routed)
    assert exhausted.route_to is None
    assert exhausted.reason == "budget-exhausted"
    rule_ids = {finding["rule"] for row in spends for finding in row.findings}
    assert {"L2.stop_conditions_required", "L2.escalation_rules_required"} <= rule_ids


def _rejected_variant(body: str, attempt: int) -> str:
    return body.replace("emits a structured report.", f"emits a structured report v{attempt}.")


def test_emitted_then_edited_spec_waits_stale(
    spec_text: str, agent_text: str, target: Path
) -> None:
    """A closed run does not reopen the evidence. Editing the spec after a
    successful emit invalidates generation, and the artifact built from the
    superseded spec reads as stale instead of being re-promoted under the new
    epoch's empty stamp set."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    result = _drive(pipeline, request, {"create-spec": spec_text, "generate-agent": agent_text})
    assert result.disposition is Disposition.EMITTED

    spec_path = result.run_dir / "spec" / "code-reviewer.spec.md"
    spec_path.write_text(_mutated_spec(spec_text), encoding="utf-8")

    resumed = compose(request, pipeline)
    assert resumed.disposition is Disposition.WAITING
    assert resumed.stage == "generate-agent"
    assert resumed.reason == "stale-artifact"


def test_blocked_then_fixed_spec_waits_without_spending(
    spec_text: str, rejected_agent_text: str, target: Path
) -> None:
    """A budget exhausted in one epoch is not re-spendable on the artifacts that
    exhausted it. After a fix to the spec, the next run asks for a new artifact
    and charges nothing for the ones already rejected."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)
    content = {"create-spec": spec_text, "generate-agent": rejected_agent_text}
    blocked = _drive(pipeline, request, content)
    assert blocked.disposition is Disposition.BLOCKED
    assert blocked.reason == "budget-exhausted"

    log = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl")
    spent = sum(1 for row in log.records() if row.kind == "spend")
    assert spent == pipeline.max_attempts

    spec_path = blocked.run_dir / "spec" / "code-reviewer.spec.md"
    spec_path.write_text(_mutated_spec(spec_text), encoding="utf-8")

    resumed = compose(request, pipeline)
    assert resumed.disposition is Disposition.WAITING
    assert resumed.stage == "generate-agent"
    assert resumed.reason in ("stale-artifact", "awaiting-artifact")
    assert sum(1 for row in log.records() if row.kind == "spend") == spent


def test_blocked_then_unchanged_rerun_does_not_replay_the_budget(
    target: Path, shipped_document: dict[str, Any]
) -> None:
    """A new epoch grants a fresh budget, never fresh evidence. Re-running an
    exhausted run over untouched files re-gates the artifact its stamps resolve to
    and stops there, asking for new content — it does not walk the whole repair
    loop a second time to re-reach verdicts already in the log."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())

    def script(request: GenerationRequest) -> str | None:
        if request.kind == "create":
            return SPEC_TEXT
        return _rejected_variant(REJECTED_AGENT_TEXT, request.attempt)

    request = ComposeRequest(name="code-reviewer", target=target)
    blocked = compose(request, pipeline, generator=FakeGenerator(script))
    assert blocked.disposition is Disposition.BLOCKED
    assert blocked.attempts_spent == pipeline.max_attempts

    log = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl")
    spent = sum(1 for row in log.records() if row.kind == "spend")

    resumed = compose(request, pipeline)
    assert resumed.disposition is Disposition.WAITING
    assert resumed.stage == "generate-agent"
    assert resumed.reason == "stale-artifact"
    assert resumed.attempts_spent == 1
    assert sum(1 for row in log.records() if row.kind == "spend") == spent + 1


def test_success_at_a_later_attempt_repromotes_from_that_artifact(
    target: Path, agent_text: str
) -> None:
    """The payload a producing stage stands behind is the one its own stamp
    records, not whatever sits at the current attempt's path. A target deleted
    after a repair loop is re-promoted from the artifact that actually passed,
    and nothing is regenerated."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())

    def script(request: GenerationRequest) -> str | None:
        if request.kind == "create":
            return SPEC_TEXT
        if request.attempt < 3:
            return _rejected_variant(REJECTED_AGENT_TEXT, request.attempt)
        return agent_text

    request = ComposeRequest(name="code-reviewer", target=target)
    result = compose(request, pipeline, generator=FakeGenerator(script))
    assert result.disposition is Disposition.EMITTED
    assert result.attempts_spent == 2

    log = RunLog(run_dir(pipeline.pipeline, target) / "run.jsonl")
    passing = [
        row
        for row in log.records()
        if row.kind == "stamp" and row.stage == "generate-agent" and row.verdict == Level.PASS.name
    ]
    assert passing[-1].path is not None
    assert "attempt-3" in Path(passing[-1].path).parts

    target.unlink()
    spent = sum(1 for row in log.records() if row.kind == "spend")

    resumed = compose(request, pipeline)
    assert resumed.disposition is Disposition.EMITTED
    assert target.read_text(encoding="utf-8") == agent_text
    assert sum(1 for row in log.records() if row.kind == "spend") == spent


def test_a_foreign_verdict_token_never_grants_a_skip(spec_text: str, target: Path) -> None:
    """Only PASS and WARN certify. A stamp carrying anything else — a torn write,
    a hand-edited log — makes its stage re-run rather than silently clearing it."""
    pipeline = PipelineSpec.from_mapping(judge_less_document())
    request = ComposeRequest(name="code-reviewer", target=target)

    result = compose(request, pipeline)
    _write(result, spec_text)
    result = compose(request, pipeline)
    assert result.stage == "generate-agent"

    log_path = run_dir(pipeline.pipeline, target) / "run.jsonl"
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    first = next(row for row in rows if row["stage"] == "gate-a")
    assert first["verdict"] == Level.PASS.name
    for row in rows:
        if row["stage"] == "gate-a" and row["kind"] == "stamp":
            row["verdict"] = "SETTLED"
    log_path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8"
    )

    resumed = compose(request, pipeline)
    assert resumed.stage == "generate-agent"
    gate_a = [row for row in RunLog(log_path).records() if row.kind == "stamp"]
    assert [row.verdict for row in gate_a if row.stage == "gate-a"] == ["SETTLED", Level.PASS.name]
