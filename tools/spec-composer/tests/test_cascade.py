"""Cascade fitness: a cheap gate FAIL must keep the expensive judge stage unreached."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import REJECTED_AGENT_TEXT, SPEC_TEXT
from spec_judge.evaluator import EvalRequest, EvalResult
from spec_linter import Level

from spec_composer.contract import PipelineSpec
from spec_composer.engine import compose
from spec_composer.generator import FakeGenerator
from spec_composer.models import ComposeRequest, Disposition, GenerationRequest


def test_judge_unreachable_after_gate_fail(target: Path, shipped_document: dict[str, Any]) -> None:
    pipeline = PipelineSpec.from_mapping({**shipped_document, "max_attempts": 1})

    def script(request: GenerationRequest) -> str | None:
        return SPEC_TEXT if request.kind == "create" else REJECTED_AGENT_TEXT

    class _CountingEvaluator:
        name = "counting"

        def __init__(self) -> None:
            self.calls = 0

        def evaluate(self, request: EvalRequest) -> EvalResult:
            self.calls += 1
            raise AssertionError("the judge stage must not run once a cheaper gate already failed")

    evaluator = _CountingEvaluator()
    request = ComposeRequest(name=target.stem, target=target)
    result = compose(request, pipeline, generator=FakeGenerator(script), evaluator=evaluator)

    assert result.disposition is Disposition.BLOCKED
    assert result.trail[-1].stage == "gate-b"
    assert result.trail[-1].verdict.level is Level.FAIL
    assert evaluator.calls == 0
