"""Panel: seat composition per tier, the fault-seeker invariant, and arbiter wiring."""

from __future__ import annotations

import pytest

from _helpers import concern, evaluator_from, result
from spec_judge.contracts import EvalSubject, Rubric
from spec_judge.evaluator import FakeEvaluator
from spec_judge.panel import Panel


def test_smoke_is_one_fault_seeker() -> None:
    panel = Panel.smoke(evaluator=evaluator_from({}))
    assert panel.tier == "smoke"
    assert [s.role for s in panel.seats] == ["fault-seeker"]


def test_every_tier_has_a_fault_seeker() -> None:
    for tier in ("smoke", "standard", "high-assurance"):
        panel = Panel.for_tier(tier, evaluator=evaluator_from({}))
        assert any(s.role == "fault-seeker" for s in panel.seats), tier


def test_high_assurance_adds_one_cross_model_fault_seeker_and_ends_with_arbiter() -> None:
    panel = Panel.high_assurance(evaluator=evaluator_from({}))
    cross = [s for s in panel.seats if s.cross_model]
    assert len(cross) == 1
    assert cross[0].role == "fault-seeker"
    assert cross[0].model  # a concrete, different alt model
    assert panel.seats[-1].role == "arbiter"


def test_for_tier_rejects_unknown_tier() -> None:
    with pytest.raises(ValueError):
        Panel.for_tier("nonsense", evaluator=evaluator_from({}))


def test_arbiter_receives_prior_seats_concerns() -> None:
    seen: dict[str, tuple] = {}

    def script(request):
        seen[request.role] = request.peer_concerns
        raised = [] if request.role == "arbiter" else [concern("B1", "low")]
        return result(request.role, cross_model=request.cross_model, concerns=raised)

    panel = Panel.standard(evaluator=FakeEvaluator(script))
    panel.evaluate(
        EvalSubject(artifact_text="a", contract_summary="c", source_spec_id="x"), Rubric()
    )

    assert seen["fault-seeker"] == ()  # first seat sees no peers
    assert len(seen["arbiter"]) >= 1  # arbiter sees earlier seats' concerns
