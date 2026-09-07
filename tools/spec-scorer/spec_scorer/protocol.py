"""ScoringContract protocol — the interface the engine measures against.

A ScoringContract is pure policy: it declares WHICH dimensions are measured and
HOW, and names its own version and evidence sources. The engine (`engine.py`) is
pure mechanism: it drives a contract over an artifact and assembles the
ScoreCard. Neither knows any usage context — the same mechanism/policy split the
Linter and Judger already make.

`measure` is the static pass (dimensions read directly from the artifact and any
injected repo facts). `fold` is the optional behavioral pass: it turns a
pre-computed Judger `Verdict` into behavioral dimensions. A contract with no
behavioral view returns an empty list from `fold`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .scorecard import DimensionScore

if TYPE_CHECKING:
    from spec_linter import Verdict


@runtime_checkable
class ScoringContract(Protocol):
    name: str
    version: str
    sources: list[str]

    def parse(self, artifact: Any) -> Any:
        """Turn a raw artifact (mapping or text) into a measurable object, or
        raise to signal an unparseable artifact. Unlike the Linter, the Scorer
        has nothing to measure on an unparseable artifact, so the caller treats
        a raise as an operational error, not a low score."""
        ...

    def measure(self, parsed: Any) -> list[DimensionScore]:
        """Return the static-pass dimensions for a parsed artifact. Dimensions
        whose evidence source was not supplied are omitted, never zeroed."""
        ...

    def fold(
        self, verdict: Verdict, parsed: Any, artifact_text: str | None
    ) -> list[DimensionScore]:
        """Return behavioral dimensions folded from a Judger verdict. Empty when
        the contract has no behavioral view."""
        ...
