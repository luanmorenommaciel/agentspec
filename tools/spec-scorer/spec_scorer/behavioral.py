"""Behavioral fold — a Judger `Verdict` into Behavioral Quality dimensions.

What a `Verdict` actually carries at the Scorer's boundary is *less* than it
looks. Reading `spec_judge.consensus`: per-seat `confidence` is discarded during
consensus, and severity is compressed — `low` and `medium` both map to `WARN`
before a `WARN` cap demotes `high` too, so in a smoke- or standard-tier verdict
**every finding is WARN**. Only the rule category survives intact.

So Finding Density is measured as **category presence**, not severity-weighted
density: of the four behavioral categories (B1 vagueness, B2 capability-not-
delivered, B3 internal-contradiction, B4 intent-drift), how many are *absent*.
Category presence is also the signal most robust to panel size — more seats may
corroborate a category but cannot manufacture new kinds of defect — which is why
it survives the seat-count normalization problem that a raw count would not.

Reaching past the `Verdict` to `EvalResult` to recover raw severity is
deliberately not done: the WARN cap is the Judger's calibration (ADR-003 §3.5),
and a score that undoes it could imply an artifact is worse than any gate will
say.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .scorecard import DimensionScore

if TYPE_CHECKING:
    from spec_linter import Verdict

_BEHAVIORAL_CATEGORIES = ("B1", "B2", "B3", "B4")


def _category_of(rule: str) -> str:
    """The category prefix of a finding rule: 'B1.vagueness' -> 'B1'."""
    return rule.split(".", 1)[0]


def fold_behavioral(verdict: Verdict, artifact_text: str | None = None) -> list[DimensionScore]:
    """Fold a Judger verdict into a single Behavioral Quality dimension.

    Absent behavioral evidence is signalled by returning an empty list (the
    engine only calls this when a verdict was supplied). A clean verdict — no
    behavioral findings — scores 4/4: absence of concern is the best behavioral
    result, never a zero.
    """
    present = {
        _category_of(f.rule)
        for f in verdict.findings
        if _category_of(f.rule) in _BEHAVIORAL_CATEGORIES
    }
    clean = [c for c in _BEHAVIORAL_CATEGORIES if c not in present]
    counts = {
        c: sum(1 for f in verdict.findings if _category_of(f.rule) == c)
        for c in sorted(present)
    }
    detail = (
        "categories raised: " + ", ".join(f"{c}×{n}" for c, n in counts.items())
        if counts
        else "no behavioral categories raised"
    )
    return [
        DimensionScore(
            dimension="behavioral_cleanliness",
            family="Behavioral Quality",
            numerator=len(clean),
            denominator=len(_BEHAVIORAL_CATEGORIES),
            detail=detail,
        )
    ]
