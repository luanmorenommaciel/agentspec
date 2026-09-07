"""ScoreCard — the structured, human-readable result of a scoring run.

The Scorer's counterpart to the Linter's `Verdict`. A `Verdict` decides
(PASS/WARN/FAIL); a `ScoreCard` *describes* — it never gates. It carries one
`DimensionScore` per measured dimension plus the provenance metadata that makes
two ScoreCards detectably (non-)comparable: when they were measured, against
which contract version, at which Judger tier, and from which evidence sources.

There is deliberately **no composite score**: a single roll-up reintroduces the
uninterpretable number the multi-dimensional design exists to avoid. Family
roll-ups are possible only under caller-supplied weights (policy), never a
built-in default — so this module offers grouping (`by_family`), not a total.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class CheckItem(BaseModel):
    """One checkpoint inside a dimension — what `--explain` prints per topic.

    Two kinds. A `bool` check either holds or not (rendered ✓/✗): the topics of
    `completeness`, `convention_conformance`, `mitigation_coverage`,
    `maturity_conformance`, `reference_integrity`, and `behavioral_cleanliness`.
    A `points` check contributes a magnitude (rendered `+N`): the components of
    `risk_surface` and the count-based `actual_reuse`.

    `contribution` is what this topic added to its dimension's numerator (0/1 for
    a bool, the points for a `points` check). `note` carries the raw value that
    produced it (`false`, `T2`, `3 inbound`), so the number never floats free of
    its evidence — the same discipline the dimension ratio follows.
    """

    model_config = ConfigDict(frozen=True)

    label: str
    contribution: int
    kind: Literal["bool", "points"] = "bool"
    note: str = ""

    def render(self) -> str:
        if self.kind == "bool":
            mark = "✓" if self.contribution > 0 else "✗"
            line = f"    {mark} {self.label}"
        else:
            line = f"    +{self.contribution}  {self.label}"
        if self.note:
            line += f" ({self.note})"
        return line


class DimensionScore(BaseModel):
    """One measured quality dimension, expressed as a ratio with raw counts.

    `numerator / denominator` is the score; both counts stay visible so the
    number never floats free of its evidence (`12/12`, `5/7`). A measured ratio
    carries genuine resolution — unlike a judged `9.8`.

    `higher_is_better` records polarity: most dimensions improve toward 1.0, but
    `risk_surface` does not (more surface is more risk, not a better artifact).
    The flag lets a consumer interpret the ratio without hard-coding per-dimension
    knowledge; the engine and ScoreCard stay polarity-agnostic.
    """

    model_config = ConfigDict(frozen=True)

    dimension: str
    family: str
    numerator: int
    denominator: int
    higher_is_better: bool = True
    detail: str = ""
    checks: list[CheckItem] = []

    @property
    def applicable(self) -> bool:
        """False when nothing was measurable (denominator 0) — the dimension is
        present as provenance but carries no ratio."""
        return self.denominator > 0

    @property
    def ratio(self) -> float | None:
        """The score in 0..1, or None when not applicable (denominator 0)."""
        return self.numerator / self.denominator if self.denominator > 0 else None

    def render(self, explain: bool = False) -> str:
        polarity = "" if self.higher_is_better else "  (higher = more risk)"
        if not self.applicable:
            body = "n/a"
        else:
            body = f"{self.ratio:.2f}  [{self.numerator}/{self.denominator}]"
        line = f"  {self.dimension:<22} {body}{polarity}"
        if explain and self.checks:
            # Per-topic breakdown supersedes the terse detail line.
            for item in self.checks:
                line += f"\n{item.render()}"
        elif self.detail:
            line += f"\n{'':<24}{self.detail}"
        return line


class ScoreCard(BaseModel):
    """The full analytical result: measured dimensions + their provenance.

    The metadata is load-bearing, not decoration. `contract_name`,
    `contract_version`, and `judger_tier` are what let a consumer refuse to
    compare a smoke-tier card against a high-assurance one, or cards scored
    against different contracts — `contract_version` alone cannot distinguish two
    contracts that share a version string, which is why the contract's `name`
    travels too. These are the comparability traps the Scorer must not paper over.
    """

    model_config = ConfigDict(frozen=True)

    dimensions: list[DimensionScore]
    measured_at: str
    contract_name: str
    contract_version: str
    judger_tier: str | None = None
    evidence_sources: list[str]

    def by_family(self) -> dict[str, list[DimensionScore]]:
        """Group dimensions by family, preserving first-seen family order."""
        grouped: dict[str, list[DimensionScore]] = {}
        for dim in self.dimensions:
            grouped.setdefault(dim.family, []).append(dim)
        return grouped

    def render(self, explain: bool = False) -> str:
        """Render the card. `explain=True` expands each dimension into its
        per-topic checkpoints (✓/✗ for boolean checks, `+N` for weighted ones);
        the compact default prints only the ratios and terse detail lines."""
        tier = self.judger_tier or "none"
        header = (
            f"SCORECARD  (contract {self.contract_name} {self.contract_version}, "
            f"judger_tier={tier}, sources={', '.join(self.evidence_sources)})"
        )
        if not self.dimensions:
            return f"{header}\n  (no dimensions measured)"
        lines = [header]
        for family, dims in self.by_family().items():
            lines.append(f"— {family}")
            lines.extend(dim.render(explain) for dim in dims)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render(explain=False)
