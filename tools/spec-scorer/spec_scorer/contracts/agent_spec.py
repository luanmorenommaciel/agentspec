"""Agent-spec scoring contract (authored as code).

The reference scoring policy for AgentSpec agents, the sibling of the Linter's
`AgentSpecContract`. It reuses the Linter's `AgentSpec` model to parse, then maps
the parsed spec onto the V0 dimension set across three static families, plus an
optional Behavioral Quality fold when a Judger verdict is supplied.

Repo-dependent dimensions (reference integrity, actual reuse) are emitted only
when their evidence was injected at construction — otherwise omitted, never
zeroed. `sources` reflects exactly which evidence streams were available, so the
ScoreCard's provenance is honest about what it could and could not see.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from spec_linter import AgentSpec

from .. import dimensions
from ..behavioral import fold_behavioral
from ..scorecard import DimensionScore

if TYPE_CHECKING:
    from spec_linter import Verdict


class AgentSpecScoringContract:
    name = "agent-spec"
    version = "0.1.0"

    def __init__(
        self,
        known_kb_domains: set[str] | None = None,
        inbound_references: dict[str, int] | None = None,
    ) -> None:
        """`known_kb_domains` enables reference_integrity; `inbound_references`
        (spec id -> inbound count) enables actual_reuse. Omitting either drops
        its dimension rather than scoring it zero."""
        self._known_kb_domains = known_kb_domains
        self._inbound_references = inbound_references
        sources: list[str] = []
        if known_kb_domains is not None:
            sources.append("kb-index")
        if inbound_references is not None:
            sources.append("repo-graph")
        self.sources = sources

    def parse(self, artifact: Any) -> AgentSpec:
        """Validate the artifact into an `AgentSpec`, reusing the Linter's model.

        A raise signals an unparseable artifact: the Scorer has nothing to
        measure, and the CLI reports it as an operational error (exit 2), never
        a low score."""
        return AgentSpec.model_validate(artifact)

    def measure(self, parsed: AgentSpec) -> list[DimensionScore]:
        scores = [
            dimensions.completeness(parsed),
            dimensions.convention_conformance(parsed),
            dimensions.risk_surface(parsed),
            dimensions.mitigation_coverage(parsed),
            dimensions.maturity_conformance(parsed),
        ]
        if self._known_kb_domains is not None:
            scores.append(dimensions.reference_integrity(parsed, self._known_kb_domains))
        if self._inbound_references is not None:
            inbound = self._inbound_references.get(parsed.id, 0)
            scores.append(dimensions.actual_reuse(parsed, inbound))
        return scores

    def fold(
        self, verdict: Verdict, parsed: AgentSpec, artifact_text: str | None
    ) -> list[DimensionScore]:
        return fold_behavioral(verdict, artifact_text)
