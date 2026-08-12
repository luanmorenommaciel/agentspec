"""Scoring engine — pure mechanism, one entry point.

`score(artifact, contract) -> ScoreCard` mirrors `lint(artifact, contract)` and
`judge(artifact, contract, panel)`. The engine has ZERO knowledge of what any
dimension means: the contract parses and measures, the engine only sequences the
passes and stamps provenance.

Determinism: given the same artifact, contract, and (optional) verdict, the
*dimensions* are byte-identical across runs — there is no network, no model call,
no randomness anywhere on this path. The only non-deterministic field is
`measured_at`, which is provenance, not a score; inject `now` to pin it (the
determinism test does exactly that).

The Judger tier is passed alongside the verdict rather than read from it: a
`Verdict` does not carry its tier, and that tier is exactly the metadata a
consumer needs to decide whether two ScoreCards are comparable. Making the
caller supply it keeps that fact explicit instead of silently absent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .protocol import ScoringContract
from .scorecard import ScoreCard

if TYPE_CHECKING:
    from spec_linter import Verdict


def score(
    artifact: Any,
    contract: ScoringContract,
    *,
    verdict: Verdict | None = None,
    judger_tier: str | None = None,
    artifact_text: str | None = None,
    now: datetime | None = None,
) -> ScoreCard:
    parsed = contract.parse(artifact)
    dimensions = list(contract.measure(parsed))
    sources = ["artifact", *contract.sources]
    if verdict is not None:
        dimensions.extend(contract.fold(verdict, parsed, artifact_text))
        sources.append("judger")
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    return ScoreCard(
        dimensions=dimensions,
        measured_at=stamp,
        contract_version=contract.version,
        judger_tier=judger_tier,
        evidence_sources=sources,
    )
