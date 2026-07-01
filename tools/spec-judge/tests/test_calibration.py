"""Confirmation harness (the Judger ADR, issue #57, §6): the engine is a fitness function.

Driven by scripted evaluators — this proves the ENGINE's wiring discriminates
(degraded → WARN, good → PASS) and that the orchestration is *sensitive* to the
fault-seeker. It does not prove a real model out-finds a real balanced reviewer;
that is the key-gated live run's job (``test_openrouter_live``).
"""

from __future__ import annotations

import pathlib

import pytest

from _helpers import concern, result
from spec_linter import Level

from spec_judge.contracts import SpecConformanceContract, split_frontmatter
from spec_judge.engine import judge
from spec_judge.evaluator import FakeEvaluator
from spec_judge.panel import Panel, Seat

_CALIBRATION = pathlib.Path(__file__).resolve().parents[1] / "examples" / "calibration"

# self-contained fixture -> the defect a competent fault-seeker should raise (None = clean)
_FIXTURES = {
    "b1_vagueness.md": "B1",
    "b2_capability_not_delivered.md": "B2",
    "b3_internal_contradiction.md": "B3",
    "b4_intent_drift.md": "B4",
    "good_clean.md": None,
}


def _load(filename: str) -> tuple[dict, str]:
    spec, body = split_frontmatter((_CALIBRATION / filename).read_text())
    assert spec is not None, f"{filename} must carry frontmatter"
    return spec, body


def _scripted(expected: str | None) -> FakeEvaluator:
    """A competent panel: the fault-seeker raises the fixture's defect; peers stay clean."""

    def script(request):
        if request.role == "fault-seeker" and expected is not None:
            return result(
                request.role, cross_model=request.cross_model, concerns=[concern(expected, "high")]
            )
        return result(request.role, cross_model=request.cross_model)

    return FakeEvaluator(script)


@pytest.mark.parametrize("filename,expected", list(_FIXTURES.items()))
def test_engine_discriminates(filename: str, expected: str | None) -> None:
    spec, body = _load(filename)
    verdict = judge(
        body, SpecConformanceContract(spec), Panel.standard(evaluator=_scripted(expected))
    )
    if expected is None:
        assert verdict.level == Level.PASS
    else:
        assert verdict.level >= Level.WARN
        assert expected in {f.rule.split(".", 1)[0] for f in verdict.findings}


def test_fault_seeker_earns_its_cost() -> None:
    """Isolate the panel-composition variable: the SAME scripted evaluator backs both
    arms (it only ever raises the fixture's defect when asked in the fault-seeker
    role), so a lower detection rate with the fault-seeker seat removed cannot be an
    artifact of the script — it can only come from the panel no longer asking anyone
    to play that role."""
    degraded = [(name, cat) for name, cat in _FIXTURES.items() if cat is not None]

    def warn_rate(build_panel) -> float:
        flagged = 0
        for name, cat in degraded:
            spec, body = _load(name)
            verdict = judge(body, SpecConformanceContract(spec), build_panel(_scripted(cat)))
            flagged += int(verdict.level >= Level.WARN)
        return flagged / len(degraded)

    with_fault_seeker = warn_rate(lambda ev: Panel.standard(evaluator=ev))
    # Tier label is "standard" (not a made-up name): consensus() now validates tier
    # against the canonical set, and only the seat composition is under test here —
    # this ad hoc panel is the standard panel with its fault-seeker seat removed.
    ablated = warn_rate(lambda ev: Panel("standard", [Seat(role="conformance-checker")], ev))
    assert with_fault_seeker > ablated  # removing the fault-seeker measurably lowers detection
