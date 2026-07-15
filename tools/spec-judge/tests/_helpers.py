"""Builders for scripted evaluators in tests (no network, fully deterministic)."""

from __future__ import annotations

from collections.abc import Iterable

from spec_judge.evaluator import Concern, EvalRequest, EvalResult, FakeEvaluator


def concern(
    category: str,
    severity: str = "high",
    *,
    evidence: str = "ev",
    expected: str = "exp",
    recommendation: str = "fix",
) -> Concern:
    return Concern(
        category=category,
        severity=severity,
        evidence=evidence,
        expected=expected,
        recommendation=recommendation,
    )


def result(
    role: str,
    *,
    cross_model: bool = False,
    confidence: float = 0.9,
    concerns: Iterable[Concern] = (),
    model: str = "default-model",
) -> EvalResult:
    return EvalResult(
        role=role,
        model=model,
        cross_model=cross_model,
        confidence=confidence,
        concerns=tuple(concerns),
    )


def evaluator_from(mapping: dict[tuple[str, bool], EvalResult]) -> FakeEvaluator:
    """Build a FakeEvaluator that returns a scripted result per ``(role, cross_model)``.

    Unmapped seats return a clean, high-confidence result (no concerns).
    """

    def script(request: EvalRequest) -> EvalResult:
        key = (request.role, request.cross_model)
        if key in mapping:
            return mapping[key]
        return result(request.role, cross_model=request.cross_model, confidence=0.95)

    return FakeEvaluator(script)
