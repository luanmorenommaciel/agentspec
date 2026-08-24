"""Engine: default bindings, judge disposition mapping, and the offline lifecycle."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from conftest import AGENT_TEXT, REJECTED_AGENT_TEXT, SPEC_TEXT, judge_less_document
from spec_judge.evaluator import Concern, EvalRequest, EvalResult, FakeEvaluator
from spec_linter import Level

from spec_composer.contract import PipelineSpec
from spec_composer.engine import compose, nearest_producer
from spec_composer.generator import FakeGenerator
from spec_composer.models import ComposeRequest, Disposition, GenerationRequest
from spec_composer.runstate import RunLog

_UNPARSEABLE_SUBJECT_PIPELINE = {
    "pipeline": "inline-unparseable-judge-subject",
    "version": 1,
    "max_attempts": 3,
    "archive": ".claude/sdd/archive/specs/{name}/",
    "stages": [
        {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
        {"id": "gate-a", "kind": "lint", "input_contract": "creation-spec"},
        {
            "id": "generate-agent",
            "kind": "generate",
            "input_contract": "creation-spec",
            "output_contract": "agent-spec",
        },
        {"id": "gate-b", "kind": "lint", "input_contract": "agent-spec"},
        {"id": "generate-empty", "kind": "generate"},
        {"id": "judge-agent", "kind": "judge", "judge_tier": "standard"},
    ],
}

_INLINE_JUDGE_LESS_PIPELINE = {
    "pipeline": "inline-agent-creation",
    "version": 1,
    "max_attempts": 3,
    "archive": ".claude/sdd/archive/specs/{name}/",
    "stages": [
        {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
        {"id": "gate-a", "kind": "lint", "input_contract": "creation-spec"},
        {
            "id": "generate-agent",
            "kind": "generate",
            "input_contract": "creation-spec",
            "output_contract": "agent-spec",
        },
        {"id": "gate-b", "kind": "lint", "input_contract": "agent-spec"},
        {"id": "emit-agent", "kind": "emit", "require_approval_for": []},
    ],
}


def _generate_script(request: GenerationRequest) -> str | None:
    return SPEC_TEXT if request.kind == "create" else AGENT_TEXT


def _with_judge_tier(document: dict[str, Any], tier: str) -> dict[str, Any]:
    stages = []
    for entry in document["stages"]:
        updated = dict(entry)
        if updated.get("id") == "judge-agent":
            updated["judge_tier"] = tier
        stages.append(updated)
    return {**document, "stages": stages}


def _clean_result(role: str, *, cross_model: bool = False, confidence: float = 0.95) -> EvalResult:
    return EvalResult(role=role, model="test-model", cross_model=cross_model, confidence=confidence)


def _unreachable_evaluate(request: EvalRequest) -> EvalResult:
    raise AssertionError("the panel must not run once the subject failed to parse")


def test_compose_returns_trail_with_default_bindings(
    target: Path, written_spec: Path, shipped_document: dict[str, Any]
) -> None:
    request = ComposeRequest(name=target.stem, target=target, spec_path=written_spec)
    pipeline = PipelineSpec.from_mapping(shipped_document)
    result = compose(request, pipeline)
    assert result.disposition is Disposition.WAITING
    assert {entry.stage for entry in result.trail} == {"create-spec", "gate-a"}
    assert all(entry.verdict.level is Level.PASS for entry in result.trail)
    assert result.expected_path is not None


def test_judge_fail_is_stamped_before_blocked(
    target: Path, shipped_document: dict[str, Any]
) -> None:
    pipeline = PipelineSpec.from_mapping(_with_judge_tier(shipped_document, "high-assurance"))

    def evaluate(request: EvalRequest) -> EvalResult:
        if request.role == "conformance-checker":
            return _clean_result(request.role)
        concern = Concern(
            category="B2", severity="high", evidence="ev", expected="exp", recommendation="fix"
        )
        return EvalResult(
            role=request.role,
            model="test-model",
            cross_model=request.cross_model,
            confidence=0.9,
            concerns=(concern,),
        )

    request = ComposeRequest(name=target.stem, target=target)
    result = compose(
        request,
        pipeline,
        generator=FakeGenerator(_generate_script),
        evaluator=FakeEvaluator(evaluate),
    )

    assert result.disposition is Disposition.BLOCKED
    assert result.reason == "high-assurance-judge-fail"
    assert result.trail[-1].verdict.level is Level.FAIL

    log = RunLog(result.run_dir / "run.jsonl")
    stamps = [row for row in log.records() if row.kind == "stamp" and row.stage == "judge-agent"]
    assert stamps
    assert stamps[-1].verdict == "FAIL"


def test_capped_tier_unparseable_is_error_not_high_assurance(target: Path) -> None:
    pipeline = PipelineSpec.from_mapping(_UNPARSEABLE_SUBJECT_PIPELINE)

    def script(request: GenerationRequest) -> str | None:
        if request.kind == "create":
            return SPEC_TEXT
        return AGENT_TEXT if request.stage == "generate-agent" else ""

    request = ComposeRequest(name=target.stem, target=target)
    result = compose(
        request,
        pipeline,
        generator=FakeGenerator(script),
        evaluator=FakeEvaluator(_unreachable_evaluate),
    )

    assert result.disposition is Disposition.ERROR
    assert result.reason == "judge-unparseable"
    assert result.trail[-1].verdict.level is Level.FAIL
    assert result.trail[-1].verdict.findings[0].rule == "spec-conformance:code-reviewer.unparseable"


def test_judge_less_pipeline_emits(target: Path) -> None:
    pipeline = PipelineSpec.from_mapping(_INLINE_JUDGE_LESS_PIPELINE)
    request = ComposeRequest(name=target.stem, target=target)
    result = compose(request, pipeline, generator=FakeGenerator(_generate_script))
    assert result.disposition is Disposition.EMITTED
    assert result.artifact == target
    assert target.read_text(encoding="utf-8") == AGENT_TEXT


def test_run_completes_without_provider_credentials(
    target: Path, shipped_document: dict[str, Any]
) -> None:
    assert os.environ.get("OPENROUTER_API_KEY") is None
    pipeline = PipelineSpec.from_mapping(shipped_document)

    def evaluate(request: EvalRequest) -> EvalResult:
        return _clean_result(request.role, cross_model=request.cross_model)

    request = ComposeRequest(name=target.stem, target=target)
    result = compose(
        request,
        pipeline,
        generator=FakeGenerator(_generate_script),
        evaluator=FakeEvaluator(evaluate),
    )
    assert result.disposition is Disposition.EMITTED
    assert result.artifact == target


def test_nearest_producer_returns_none_before_first_stage(
    shipped_document: dict[str, Any],
) -> None:
    pipeline = PipelineSpec.from_mapping(shipped_document)
    assert nearest_producer(pipeline, 0) == (-1, None)


def test_nearest_producer_finds_closest_preceding_producer(
    shipped_document: dict[str, Any],
) -> None:
    pipeline = PipelineSpec.from_mapping(shipped_document)
    index, stage = nearest_producer(pipeline, 3)
    assert index == 2
    assert stage is not None
    assert stage.id == "generate-agent"


def test_warn_judge_verdict_does_not_block(target: Path, shipped_document: dict[str, Any]) -> None:
    pipeline = PipelineSpec.from_mapping(shipped_document)

    def evaluate(request: EvalRequest) -> EvalResult:
        if request.role != "fault-seeker":
            return _clean_result(request.role)
        concern = Concern(
            category="B1", severity="low", evidence="ev", expected="exp", recommendation="fix"
        )
        return EvalResult(
            role=request.role, model="test-model", confidence=0.9, concerns=(concern,)
        )

    request = ComposeRequest(name=target.stem, target=target)
    result = compose(
        request,
        pipeline,
        generator=FakeGenerator(_generate_script),
        evaluator=FakeEvaluator(evaluate),
    )

    assert result.disposition is Disposition.EMITTED
    judge_verdicts = [entry.verdict for entry in result.trail if entry.stage == "judge-agent"]
    assert judge_verdicts[-1].level is Level.WARN


def test_emit_promotes_only_after_gate_passes(target: Path) -> None:
    pipeline = PipelineSpec.from_mapping(judge_less_document())

    def script(request: GenerationRequest) -> str | None:
        if request.kind == "create":
            return SPEC_TEXT
        return AGENT_TEXT if request.attempt >= 2 else REJECTED_AGENT_TEXT

    request = ComposeRequest(name=target.stem, target=target)
    result = compose(request, pipeline, generator=FakeGenerator(script))
    assert result.disposition is Disposition.EMITTED
    assert target.read_text(encoding="utf-8") == AGENT_TEXT
