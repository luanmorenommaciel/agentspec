"""Spec Scorer — deterministic, multi-dimensional artifact scoring (ADR-011).

The analytical, non-gating third member of the enforcement toolchain. Where the
Linter asks "is this well-formed?" and the Judger "does this honor its contract?",
the Scorer asks "how good is this artifact?" — and answers with measured
per-dimension ratios, never a verdict.

One mechanism: `score(artifact, contract) -> ScoreCard` (`engine.py`), mirroring
`lint` and `judge`. Contracts are policy (`protocol.py`, `contracts/`);
`ScoreCard` / `DimensionScore` are the structured, provenance-carrying result. It
reuses the Linter's value objects (`AgentSpec`, `Verdict`, `Finding`) by import,
and makes no model calls — every metric is measured.
"""

from .contracts import AgentSpecScoringContract
from .engine import score
from .protocol import ScoringContract
from .scorecard import CheckItem, DimensionScore, ScoreCard

__all__ = [
    "AgentSpecScoringContract",
    "CheckItem",
    "DimensionScore",
    "ScoreCard",
    "ScoringContract",
    "score",
]
