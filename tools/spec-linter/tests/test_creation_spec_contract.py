"""Tests for the creation-spec contract, run through `engine.lint`."""

from __future__ import annotations

from typing import Any

import pytest

from spec_linter.contracts.creation_spec import CreationSpecContract
from spec_linter.engine import lint
from spec_linter.protocol import Contract
from spec_linter.verdict import Level

_MISSING = object()


def _spec(**overrides: Any) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "name": "code-reviewer",
        "intent": "Review Python diffs against the house standards and report structured findings",
        "overlap_check": 0.2,
        "trigger_count": 3,
        "tier": "T2",
    }
    for key, value in overrides.items():
        if value is _MISSING:
            spec.pop(key, None)
        else:
            spec[key] = value
    return spec


@pytest.mark.parametrize(
    ("spec", "expected_rule"),
    [
        pytest.param(_spec(overlap_check=_MISSING), "L2.overlap_check", id="overlap_check-missing"),
        pytest.param(
            _spec(overlap_check="high"), "L2.overlap_check", id="overlap_check-non_numeric"
        ),
        pytest.param(_spec(overlap_check=True), "L2.overlap_check", id="overlap_check-boolean"),
        pytest.param(
            _spec(overlap_check=0.75), "L2.overlap_check", id="overlap_check-at_or_above_max"
        ),
        pytest.param(_spec(trigger_count=_MISSING), "L2.trigger_count", id="trigger_count-missing"),
        pytest.param(
            _spec(trigger_count="three"), "L2.trigger_count", id="trigger_count-non_integer"
        ),
        pytest.param(_spec(trigger_count=True), "L2.trigger_count", id="trigger_count-boolean"),
        pytest.param(_spec(trigger_count=2), "L2.trigger_count", id="trigger_count-below_minimum"),
        pytest.param(_spec(intent=_MISSING), "L2.intent_missing", id="intent-absent"),
        pytest.param(_spec(intent="   "), "L2.intent_missing", id="intent-blank"),
        pytest.param(_spec(intent="Fix bugs fast"), "L2.intent_unspecific", id="intent-too_short"),
        pytest.param(
            _spec(
                name="code-reviewer-for-python-pull-requests",
                intent="Code Reviewer For Python Pull Requests",
            ),
            "L2.intent_unspecific",
            id="intent-restates_name",
        ),
        pytest.param(_spec(tier="T9"), "L2.tier", id="tier-outside_allowed_set"),
        pytest.param(
            _spec(trigger_count=3, trigger_scenarios=["a", "b"]),
            "L2.trigger_count_mismatch",
            id="trigger_scenarios-fewer_than_claimed",
        ),
        pytest.param(
            _spec(trigger_count=3, trigger_scenarios=["a", "b", "c", "d"]),
            "L2.trigger_count_mismatch",
            id="trigger_scenarios-more_than_claimed",
        ),
        pytest.param(
            _spec(trigger_count=3, trigger_scenarios=[]),
            "L2.trigger_count_mismatch",
            id="trigger_scenarios-empty",
        ),
        pytest.param(
            _spec(trigger_count=3, trigger_scenarios="a, b, c"),
            "L2.trigger_count_mismatch",
            id="trigger_scenarios-not_a_list",
        ),
    ],
)
def test_gate_a_criteria(spec: dict[str, Any], expected_rule: str) -> None:
    verdict = lint(spec, CreationSpecContract())
    assert verdict.level == Level.FAIL
    assert len(verdict.findings) == 1
    finding = verdict.findings[0]
    assert finding.rule == expected_rule
    assert finding.level == Level.FAIL


def test_valid_creation_spec_has_no_findings() -> None:
    verdict = lint(_spec(), CreationSpecContract())
    assert verdict.level == Level.PASS
    assert verdict.findings == []


def test_thresholds_are_constructor_parameters() -> None:
    spec = _spec()
    assert lint(spec, CreationSpecContract()).level == Level.PASS

    strict = CreationSpecContract(
        overlap_max=0.1, min_triggers=5, min_intent_words=20, tiers=("T4", "T5")
    )
    verdict = lint(spec, strict)
    assert verdict.level == Level.FAIL
    rules = {finding.rule for finding in verdict.findings}
    assert rules == {"L2.overlap_check", "L2.trigger_count", "L2.intent_unspecific", "L2.tier"}


def test_non_mapping_is_unparseable() -> None:
    verdict = lint(["not", "a", "mapping"], CreationSpecContract())
    assert verdict.level == Level.FAIL
    assert len(verdict.findings) == 1
    assert verdict.findings[0].rule == "creation-spec.unparseable"


def test_contract_satisfies_protocol() -> None:
    assert isinstance(CreationSpecContract(), Contract)


def test_matching_trigger_scenarios_have_no_findings() -> None:
    """The enumeration is optional; declaring one that agrees with the count is
    the whole point of declaring it."""
    spec = _spec(
        trigger_count=3, trigger_scenarios=["review a PR", "review a diff", "review a file"]
    )
    verdict = lint(spec, CreationSpecContract())
    assert verdict.level == Level.PASS
    assert verdict.findings == []


def test_a_malformed_count_is_reported_once() -> None:
    """A count that is not a count is one defect, not two: the mismatch rule stays
    silent until the count it compares against is itself well-formed."""
    spec = _spec(trigger_count="three", trigger_scenarios=["a", "b"])
    verdict = lint(spec, CreationSpecContract())
    assert verdict.level == Level.FAIL
    assert [finding.rule for finding in verdict.findings] == ["L2.trigger_count"]


def test_scenarios_are_only_compared_when_declared() -> None:
    """A spec that never enumerates its triggers is judged on the count alone."""
    verdict = lint(_spec(trigger_count=4), CreationSpecContract())
    assert verdict.level == Level.PASS
