"""Consensus: concern→Finding mapping, the WARN cap, and the strict FAIL gate.

The gate is a *true three-way* AND: the same-platform fault-seeker, the cross-model
fault-seeker, and the arbiter must each independently raise a category at high
severity (plus a confidence floor). These tests pin every branch — most importantly
that a block does NOT fire when the same-platform fault-seeker is silent even though
the cross-model seat and arbiter agree.
"""

from __future__ import annotations

import pytest
from _helpers import concern, result
from spec_linter import Level

from spec_judge.consensus import FAIL_CONFIDENCE_FLOOR, concern_to_finding, consensus
from spec_judge.evaluator import EvalResult


def test_concern_maps_to_finding_fields() -> None:
    finding = concern_to_finding(
        concern(
            "B2",
            "high",
            evidence="only a summary",
            expected="writes a file",
            recommendation="write the report to disk",
        )
    )
    assert finding.level == Level.WARN  # capped, not FAIL
    assert finding.rule == "B2.capability_not_delivered"
    assert finding.found == "only a summary"
    assert finding.expected == "writes a file"
    assert finding.message == "write the report to disk"


def test_clean_panel_is_pass() -> None:
    results = [result("fault-seeker"), result("arbiter")]
    assert consensus(results, tier="standard").level == Level.PASS


def test_standard_tier_caps_high_to_warn() -> None:
    results = [
        result("fault-seeker", concerns=[concern("B1", "high")]),
        result("arbiter", concerns=[concern("B1", "high")]),
    ]
    assert consensus(results, tier="standard").level == Level.WARN


def test_smoke_tier_caps_high_to_warn() -> None:
    results = [result("fault-seeker", concerns=[concern("B2", "high")])]
    assert consensus(results, tier="smoke").level == Level.WARN


def _high_assurance(
    *,
    same: bool = True,
    cross: bool = True,
    arbiter: bool = True,
    confidence: float = 0.9,
    category: str = "B2",
) -> list[EvalResult]:
    flag = [concern(category, "high")]
    return [
        result(
            "fault-seeker", cross_model=False, confidence=confidence, concerns=flag if same else []
        ),
        result("conformance-checker", confidence=confidence),
        result(
            "fault-seeker", cross_model=True, confidence=confidence, concerns=flag if cross else []
        ),
        result("arbiter", confidence=confidence, concerns=flag if arbiter else []),
    ]


def test_fail_on_full_three_way_agreement() -> None:
    assert consensus(_high_assurance(), tier="high-assurance").level == Level.FAIL


def test_no_fail_when_same_platform_fault_seeker_silent() -> None:
    # cross-model seat + arbiter agree, but the same-platform fault-seeker is silent.
    # A two-way gate would block here; the true three-way gate must NOT.
    assert consensus(_high_assurance(same=False), tier="high-assurance").level == Level.WARN


def test_no_fail_when_cross_model_silent() -> None:
    assert consensus(_high_assurance(cross=False), tier="high-assurance").level == Level.WARN


def test_no_fail_when_arbiter_dissents() -> None:
    assert consensus(_high_assurance(arbiter=False), tier="high-assurance").level == Level.WARN


def test_no_fail_below_confidence_floor() -> None:
    below = FAIL_CONFIDENCE_FLOOR - 0.01
    assert consensus(_high_assurance(confidence=below), tier="high-assurance").level == Level.WARN


def test_at_confidence_floor_blocks() -> None:
    assert (
        consensus(_high_assurance(confidence=FAIL_CONFIDENCE_FLOOR), tier="high-assurance").level
        == Level.FAIL
    )


def test_low_confidence_extra_seat_does_not_veto_an_agreed_fail() -> None:
    # Unreachable via the 3 shipped tiers, only via the public Panel(...) constructor:
    # a 5th seat's LOW-severity concern must not drag the confidence floor down and
    # veto an otherwise fully-agreed FAIL — only HIGH-severity agreement counts toward
    # who is "agreeing" for the floor check.
    results = [
        *_high_assurance(),
        result("fault-seeker", cross_model=False, confidence=0.01, concerns=[concern("B2", "low")]),
    ]
    assert consensus(results, tier="high-assurance").level == Level.FAIL


def test_only_agreeing_category_promoted() -> None:
    # All three agree on B2; only the same-platform fault-seeker also raises B1.
    results = [
        result(
            "fault-seeker",
            cross_model=False,
            confidence=0.9,
            concerns=[concern("B2", "high"), concern("B1", "high")],
        ),
        result("fault-seeker", cross_model=True, confidence=0.9, concerns=[concern("B2", "high")]),
        result("arbiter", confidence=0.9, concerns=[concern("B2", "high")]),
    ]
    verdict = consensus(results, tier="high-assurance")
    assert verdict.level == Level.FAIL
    # Union semantics: 4 concerns in, 4 findings out. A dict keyed by `f.rule` would
    # collapse the 3 independent B2 findings into 1, masking the corroboration — pin
    # the exact counts instead.
    assert len(verdict.findings) == 4
    b2_findings = [f for f in verdict.findings if f.rule == "B2.capability_not_delivered"]
    b1_findings = [f for f in verdict.findings if f.rule == "B1.vagueness"]
    assert len(b2_findings) == 3
    assert len(b1_findings) == 1
    assert all(f.level == Level.FAIL for f in b2_findings)
    assert b1_findings[0].level == Level.WARN  # not in the agreeing set → stays capped


def test_arbiter_only_category_stays_warn() -> None:
    # The arbiter raises B3 at high severity and high confidence, but NEITHER
    # fault-seeker raised it. The arbiter alone — even decisive — cannot FAIL a
    # category: the three-way gate requires both fault-seekers to agree too.
    results = [
        result("fault-seeker", cross_model=False, confidence=0.9),
        result("fault-seeker", cross_model=True, confidence=0.9),
        result("arbiter", confidence=0.95, concerns=[concern("B3", "high")]),
    ]
    verdict = consensus(results, tier="high-assurance")
    assert verdict.level == Level.WARN
    assert len(verdict.findings) == 1
    assert verdict.findings[0].rule == "B3.internal_contradiction"
    assert verdict.findings[0].level == Level.WARN


def test_consensus_rejects_unknown_tier() -> None:
    with pytest.raises(ValueError):
        consensus([result("fault-seeker")], tier="High-Assurance")
