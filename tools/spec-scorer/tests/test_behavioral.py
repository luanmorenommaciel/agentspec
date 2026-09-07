"""Behavioral fold: category presence, not severity — and clean == best."""

from __future__ import annotations

import pytest

from spec_linter import Finding, Level, Verdict

from spec_scorer.behavioral import fold_behavioral


def test_clean_verdict_scores_full() -> None:
    """No behavioral findings -> 4/4. Absence of concern is the best result,
    never a zero."""
    dims = fold_behavioral(Verdict.from_findings([]))
    assert len(dims) == 1
    d = dims[0]
    assert (d.numerator, d.denominator) == (4, 4)
    assert d.ratio == pytest.approx(1.0)
    assert "no behavioral categories" in d.detail


def test_two_categories_present_scores_half() -> None:
    verdict = Verdict.from_findings(
        [
            Finding(level=Level.WARN, rule="B1.vagueness", message="v"),
            Finding(level=Level.WARN, rule="B3.internal_contradiction", message="c"),
        ]
    )
    d = fold_behavioral(verdict)[0]
    assert (d.numerator, d.denominator) == (2, 4)
    assert "B1×1" in d.detail
    assert "B3×1" in d.detail


def test_category_presence_saturates_across_seat_count() -> None:
    """More findings of the SAME category do not lower the score — presence,
    not count, is what the dimension measures (robust to panel size)."""
    one = Verdict.from_findings([Finding(level=Level.WARN, rule="B1.vagueness", message="v")])
    many = Verdict.from_findings(
        [Finding(level=Level.WARN, rule="B1.vagueness", message=f"v{i}") for i in range(5)]
    )
    assert fold_behavioral(one)[0].numerator == fold_behavioral(many)[0].numerator == 3


def test_non_behavioral_findings_are_ignored() -> None:
    """Structural (L2/L4) findings are not behavioral categories -> clean."""
    verdict = Verdict.from_findings(
        [Finding(level=Level.FAIL, rule="L2.stop_conditions_required", message="x")]
    )
    d = fold_behavioral(verdict)[0]
    assert d.numerator == 4  # all four behavioral categories still clean
