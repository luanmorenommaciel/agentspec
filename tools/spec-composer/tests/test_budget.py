"""Budget: the shared generation-attempt ledger across both feedback edges."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from _helpers import REJECTED_AGENT_TEXT, SPEC_TEXT, judge_less_document

from spec_composer.contract import PipelineSpec
from spec_composer.engine import compose
from spec_composer.generator import FakeGenerator
from spec_composer.models import ComposeRequest, Disposition, GenerationRequest
from spec_composer.runstate import RunLog

_BAD_SPEC_TEXT = SPEC_TEXT.replace("overlap_check: 0.21", "overlap_check: 0.95")


def _rejected_variant(attempt: int) -> str:
    return REJECTED_AGENT_TEXT.replace(
        "emits a structured report.", f"emits a structured report v{attempt}."
    )


def test_three_attempts_two_repairs_then_blocked(
    target: Path, shipped_document: dict[str, Any]
) -> None:
    pipeline = PipelineSpec.from_mapping(shipped_document)

    def script(request: GenerationRequest) -> str | None:
        return SPEC_TEXT if request.kind == "create" else _rejected_variant(request.attempt)

    request = ComposeRequest(name=target.stem, target=target)
    result = compose(request, pipeline, generator=FakeGenerator(script))

    assert result.disposition is Disposition.BLOCKED
    assert result.reason == "budget-exhausted"
    assert result.attempts_spent == 3

    log = RunLog(result.run_dir / "run.jsonl")
    spends = [row for row in log.records() if row.kind == "spend"]
    assert len(spends) == 3
    routed = [row for row in spends if row.route_to is not None]
    terminal = [row for row in spends if row.route_to is None]
    assert len(routed) == 2
    assert len(terminal) == 1
    assert terminal[0].reason == "budget-exhausted"
    assert not target.exists()


def test_budget_is_shared_across_both_edges(target: Path) -> None:
    pipeline = PipelineSpec.from_mapping(judge_less_document())

    def script(request: GenerationRequest) -> str | None:
        if request.kind == "create":
            return _BAD_SPEC_TEXT if request.attempt == 1 else SPEC_TEXT
        return _rejected_variant(request.attempt)

    request = ComposeRequest(name=target.stem, target=target)
    result = compose(request, pipeline, generator=FakeGenerator(script))

    assert result.disposition is Disposition.BLOCKED
    assert result.reason == "budget-exhausted"
    assert result.attempts_spent == 3

    log = RunLog(result.run_dir / "run.jsonl")
    spends = [row for row in log.records() if row.kind == "spend"]
    assert [row.route_to for row in spends] == ["create-spec", "generate-agent", None]


def test_exhausted_spend_records_no_route(target: Path, shipped_document: dict[str, Any]) -> None:
    pipeline = PipelineSpec.from_mapping({**shipped_document, "max_attempts": 1})

    def script(request: GenerationRequest) -> str | None:
        return SPEC_TEXT if request.kind == "create" else REJECTED_AGENT_TEXT

    request = ComposeRequest(name=target.stem, target=target)
    result = compose(request, pipeline, generator=FakeGenerator(script))

    log = RunLog(result.run_dir / "run.jsonl")
    spends = [row for row in log.records() if row.kind == "spend"]
    assert len(spends) == 1
    assert spends[-1].route_to is None
    assert spends[-1].reason == "budget-exhausted"
    assert result.disposition is Disposition.BLOCKED


def test_epoch_resets_budget_after_blocked(target: Path, shipped_document: dict[str, Any]) -> None:
    pipeline = PipelineSpec.from_mapping({**shipped_document, "max_attempts": 1})

    def script(request: GenerationRequest) -> str | None:
        return SPEC_TEXT if request.kind == "create" else REJECTED_AGENT_TEXT

    request = ComposeRequest(name=target.stem, target=target)
    first = compose(request, pipeline, generator=FakeGenerator(script))
    assert first.disposition is Disposition.BLOCKED
    assert first.epoch == 1

    second = compose(request, pipeline, generator=FakeGenerator(script))
    assert second.disposition is Disposition.BLOCKED
    assert second.epoch == first.epoch + 1
    assert second.attempts_spent == 1

    log = RunLog(second.run_dir / "run.jsonl")
    gate_a_stamps = [row for row in log.records() if row.kind == "stamp" and row.stage == "gate-a"]
    assert len(gate_a_stamps) == 1


def test_identical_reemission_after_gate_fail_terminates_at_ceiling(
    target: Path, shipped_document: dict[str, Any]
) -> None:
    """A stage that keeps being presented byte-identical rejected content after a
    gate FAIL must not wait forever: one stale-artifact wait is free, and a second
    occurrence at the same stage terminates at a ceiling instead of waiting again,
    without spending a budget attempt on the stall itself."""
    pipeline = PipelineSpec.from_mapping(shipped_document)

    def script(request: GenerationRequest) -> str | None:
        return SPEC_TEXT if request.kind == "create" else REJECTED_AGENT_TEXT

    request = ComposeRequest(name=target.stem, target=target)
    generator = FakeGenerator(script)

    first = compose(request, pipeline, generator=generator)
    print(
        f"run 1: disposition={first.disposition!r} reason={first.reason!r} "
        f"stage={first.stage!r} attempts_spent={first.attempts_spent}"
    )
    assert first.disposition is Disposition.WAITING
    assert first.reason == "stale-artifact"

    second = compose(request, pipeline, generator=generator)
    print(
        f"run 2: disposition={second.disposition!r} reason={second.reason!r} "
        f"stage={second.stage!r} attempts_spent={second.attempts_spent}"
    )
    assert second.disposition is Disposition.BLOCKED
    assert second.reason == "no-progress"
    assert second.attempts_spent == 1

    records = RunLog(second.run_dir / "run.jsonl").records()
    terminal = [(row.kind, row.reason) for row in records if row.kind in ("event", "run-closed")]
    print(f"event/run-closed rows: {terminal}")
    assert terminal == [
        ("event", "stale-artifact"),
        ("event", "no-progress"),
        ("run-closed", "no-progress"),
    ]


def test_create_edge_identical_reemission_terminates_at_ceiling(
    target: Path, shipped_document: dict[str, Any]
) -> None:
    """The `create` edge has different path semantics than `generate`: its output
    path is FIXED (the spec path itself), so re-presenting the same rejected spec
    lands the first stale wait in the SAME invocation as the gate FAIL, and the
    ceiling is reached in three invocations total — one `awaiting-artifact` wait
    for the operator to write the spec, one free `stale-artifact` wait, and a
    third that blocks — rather than the generate edge's two above."""
    pipeline = PipelineSpec.from_mapping(shipped_document)
    request = ComposeRequest(name=target.stem, target=target)

    first = compose(request, pipeline)
    print(f"run 1: disposition={first.disposition!r} reason={first.reason!r}")
    assert first.disposition is Disposition.WAITING
    assert first.reason == "awaiting-artifact"

    spec_path = first.expected_path
    assert spec_path is not None
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(_BAD_SPEC_TEXT, encoding="utf-8")

    second = compose(request, pipeline)
    print(f"run 2: disposition={second.disposition!r} reason={second.reason!r}")
    assert second.disposition is Disposition.WAITING
    assert second.reason == "stale-artifact"

    # Nothing rewrites the spec between run 2 and run 3: a habitual re-run with
    # no new information at the same fixed path.
    third = compose(request, pipeline)
    print(
        f"run 3: disposition={third.disposition!r} reason={third.reason!r} "
        f"attempts_spent={third.attempts_spent}"
    )
    assert third.disposition is Disposition.BLOCKED
    assert third.reason == "no-progress"
    assert third.attempts_spent == 1


def test_reset_after_real_progress_allows_another_stale_wait(
    target: Path, shipped_document: dict[str, Any]
) -> None:
    """Stall, then real progress, then stall again: the second stall must still
    return `waiting`, not `blocked`.

    `RunContext._stale_waits` is folded from the log once, at `__init__`. A
    stamp appended LATER IN THE SAME PROCESS — here, `create-spec`'s own stamp
    for genuinely new (still-failing) v2 content, made while a Gate A repair
    loop cycles back in-process — must reset that in-memory count the same way
    `RunLog.fold` would, or the very next stale check in that process (moments
    later, when the gate rejects v2 too and routes back again) reads the STALE
    pre-process count instead of the 0 the fresh stamp earned it, and blocks a
    producer that is still making progress one wait early."""
    pipeline = PipelineSpec.from_mapping(shipped_document)
    request = ComposeRequest(name=target.stem, target=target)

    first = compose(request, pipeline)
    assert first.disposition is Disposition.WAITING
    assert first.reason == "awaiting-artifact"

    spec_path = first.expected_path
    assert spec_path is not None
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(_BAD_SPEC_TEXT, encoding="utf-8")

    second = compose(request, pipeline)
    print(f"run 2: disposition={second.disposition!r} reason={second.reason!r}")
    assert second.disposition is Disposition.WAITING
    assert second.reason == "stale-artifact"

    # Real progress: genuinely different (still failing) bytes, so `is_fresh`
    # accepts them — simulating a host that DID rewrite the file this time,
    # unlike the ceiling test above. Gate A rejects it again (unchanged
    # `overlap_check`), routing back to `create-spec` a second time IN THE SAME
    # PROCESS as this stamp — the exact window the stale reset must survive.
    bad_spec_v2 = _BAD_SPEC_TEXT + "\nStill failing, but not the same bytes as v1.\n"
    spec_path.write_text(bad_spec_v2, encoding="utf-8")

    third = compose(request, pipeline)
    print(
        f"run 3: disposition={third.disposition!r} reason={third.reason!r} "
        f"attempts_spent={third.attempts_spent}"
    )
    assert third.disposition is Disposition.WAITING
    assert third.reason == "stale-artifact"
    assert third.attempts_spent == 2
