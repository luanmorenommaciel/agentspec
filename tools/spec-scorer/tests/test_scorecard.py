"""ScoreCard / DimensionScore value-object behavior."""

from __future__ import annotations

import pytest

from spec_scorer import DimensionScore, ScoreCard


def test_ratio_and_applicability() -> None:
    d = DimensionScore(dimension="x", family="F", numerator=3, denominator=4)
    assert d.ratio == pytest.approx(0.75)
    assert d.applicable is True


def test_zero_denominator_is_not_applicable() -> None:
    d = DimensionScore(dimension="x", family="F", numerator=0, denominator=0)
    assert d.ratio is None
    assert d.applicable is False


def test_dimension_is_frozen() -> None:
    d = DimensionScore(dimension="x", family="F", numerator=1, denominator=2)
    with pytest.raises(Exception):
        d.numerator = 2  # type: ignore[misc]


def test_scorecard_is_frozen() -> None:
    card = ScoreCard(
        dimensions=[], measured_at="t", contract_version="0.1.0", evidence_sources=["artifact"]
    )
    with pytest.raises(Exception):
        card.contract_version = "9"  # type: ignore[misc]


def test_by_family_preserves_first_seen_order() -> None:
    dims = [
        DimensionScore(dimension="a", family="Spec Quality", numerator=1, denominator=1),
        DimensionScore(dimension="b", family="Risk & Governance", numerator=1, denominator=1),
        DimensionScore(dimension="c", family="Spec Quality", numerator=1, denominator=1),
    ]
    card = ScoreCard(
        dimensions=dims, measured_at="t", contract_version="0.1.0", evidence_sources=["artifact"]
    )
    grouped = card.by_family()
    assert list(grouped.keys()) == ["Spec Quality", "Risk & Governance"]
    assert [d.dimension for d in grouped["Spec Quality"]] == ["a", "c"]


def test_no_composite_score_attribute() -> None:
    """The design forbids a default composite — there is no overall/total field."""
    card = ScoreCard(
        dimensions=[], measured_at="t", contract_version="0.1.0", evidence_sources=["artifact"]
    )
    for forbidden in ("overall", "composite", "total", "score"):
        assert not hasattr(card, forbidden)


def test_render_shows_raw_counts_and_polarity() -> None:
    good = DimensionScore(dimension="completeness", family="F", numerator=3, denominator=6)
    risk = DimensionScore(
        dimension="risk_surface", family="F", numerator=8, denominator=12, higher_is_better=False
    )
    assert "[3/6]" in good.render()
    assert "higher = more risk" in risk.render()
