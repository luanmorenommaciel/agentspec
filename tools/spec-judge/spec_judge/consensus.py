"""Consensus — pure functions that fold a panel's results into a ``Verdict``.

Two stages:

1. **Map** every concern to a ``Finding`` capped at ``WARN``. This is why the
   default is advisory: smoke and standard tiers stop here, so ``WARN`` is the
   worst verdict they can emit — ``FAIL`` is unreachable *by construction*.
2. **Promote** (high-assurance tier only) the categories that clear a strict,
   cross-checked gate from ``WARN`` to ``FAIL``.

Everything here is a pure function of the evaluators' results — no I/O, no model
vocabulary — mirroring the Linter's engine. All non-determinism lives in the
injected evaluator, never here.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from spec_linter import Finding, Level, Verdict

from .evaluator import Concern, EvalResult

_SEVERITY_TO_LEVEL = {"high": Level.FAIL, "medium": Level.WARN, "low": Level.WARN}
_CATEGORY_RULES = {
    "B1": "B1.vagueness",
    "B2": "B2.capability_not_delivered",
    "B3": "B3.internal_contradiction",
    "B4": "B4.intent_drift",
}

# Calibration knobs (ADR §7 q5): a blocking FAIL requires the weakest agreeing voice
# to clear this confidence floor, on top of the structural three-way agreement below.
FAIL_CONFIDENCE_FLOOR = 0.7
HIGH_ASSURANCE = "high-assurance"


def _rule_for(category: str) -> str:
    return _CATEGORY_RULES.get(category, f"B0.unknown_{category}")


def _category_of(rule: str) -> str:
    return rule.split(".", 1)[0]


def concern_to_finding(concern: Concern, *, cap: Level = Level.WARN) -> Finding:
    """Project one concern onto a ``Finding``, capped at ``cap`` (WARN by default).

    ``Level`` is an ``IntEnum`` ordered PASS<WARN<FAIL, so ``min`` demotes a raw
    ``high``→``FAIL`` down to the cap. The Linter's ``Finding`` is reused as-is.
    """
    raw = _SEVERITY_TO_LEVEL.get(concern.severity, Level.WARN)
    return Finding(
        level=min(raw, cap),
        rule=_rule_for(concern.category),
        message=concern.recommendation,
        expected=concern.expected,
        found=concern.evidence,
    )


def _high_categories(
    results: Iterable[EvalResult], predicate: Callable[[EvalResult], bool]
) -> set[str]:
    """Categories any matching result raised at ``high`` severity."""
    return {
        concern.category
        for result in results
        if predicate(result)
        for concern in result.concerns
        if concern.severity == "high"
    }


def _fail_gate(results: list[EvalResult]) -> set[str]:
    """Categories eligible to block. A true three-way AND across independent
    adversarial voices: the same-platform fault-seeker, the cross-model fault-seeker,
    AND the arbiter must each raise the category at ``high`` severity, and the weakest
    agreeing voice's confidence must clear the floor. Only then may a category FAIL.

    The cross-model seat is identified by its ``cross_model`` flag, not by comparing
    model names — a misconfigured alt model can never silently disable the gate.
    """
    same_fault = _high_categories(results, lambda r: r.role == "fault-seeker" and not r.cross_model)
    cross_fault = _high_categories(results, lambda r: r.role == "fault-seeker" and r.cross_model)
    arbiter = _high_categories(results, lambda r: r.role == "arbiter")
    agree = same_fault & cross_fault & arbiter
    if not agree:
        return set()
    agreeing_voices = [
        r
        for r in results
        if r.role in ("fault-seeker", "arbiter") and agree & {c.category for c in r.concerns}
    ]
    if not agreeing_voices or min(r.confidence for r in agreeing_voices) < FAIL_CONFIDENCE_FLOOR:
        return set()
    return agree


def consensus(results: list[EvalResult], tier: str) -> Verdict:
    findings = [concern_to_finding(concern) for result in results for concern in result.concerns]
    if tier == HIGH_ASSURANCE:
        promote = _fail_gate(results)
        if promote:
            findings = [
                f.model_copy(update={"level": Level.FAIL}) if _category_of(f.rule) in promote else f
                for f in findings
            ]
    return Verdict.from_findings(findings)
