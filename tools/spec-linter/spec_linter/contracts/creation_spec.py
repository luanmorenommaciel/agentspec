"""Creation-spec contract (Gate A — should this artifact exist at all).

Validates the ephemeral, pre-generation spec against the four published Gate A
criteria: the nearest existing sibling must not already cover the scope, enough
distinct triggers must be declared, the intent must be specific rather than a
restatement of the name, and the tier must be one the output template defines.
Every threshold is a constructor parameter, so revising a criterion changes call
sites rather than code.
"""

from __future__ import annotations

from typing import Any

from ..verdict import Finding, Level

_DEFAULT_TIERS = ("T1", "T2", "T3")


def _fail(rule: str, field: str, message: str, expected: str, found: str) -> Finding:
    return Finding(
        level=Level.FAIL, rule=rule, field=field, message=message, expected=expected, found=found
    )


class CreationSpecContract:
    def __init__(
        self,
        overlap_max: float = 0.60,
        min_triggers: int = 3,
        min_intent_words: int = 6,
        tiers: tuple[str, ...] = _DEFAULT_TIERS,
    ) -> None:
        self.name = "creation-spec"
        self._overlap_max = overlap_max
        self._min_triggers = min_triggers
        self._min_intent_words = min_intent_words
        self._tiers = tiers

    def parse(self, artifact: Any) -> dict[str, Any]:
        if not isinstance(artifact, dict):
            raise TypeError(f"a creation spec must be a mapping, got {type(artifact).__name__}")
        return artifact

    def check(self, parsed: dict[str, Any]) -> list[Finding]:
        return [
            *self._overlap_findings(parsed),
            *self._trigger_findings(parsed),
            *self._intent_findings(parsed),
            *self._tier_findings(parsed),
        ]

    def _overlap_findings(self, spec: dict[str, Any]) -> list[Finding]:
        value = spec.get("overlap_check")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return [
                _fail(
                    "L2.overlap_check",
                    "overlap_check",
                    "overlap_check must be a fraction between 0 and 1",
                    f"< {self._overlap_max}",
                    repr(value),
                )
            ]
        if value >= self._overlap_max:
            return [
                _fail(
                    "L2.overlap_check",
                    "overlap_check",
                    "an existing sibling already covers this scope",
                    f"< {self._overlap_max}",
                    repr(value),
                )
            ]
        return []

    def _trigger_findings(self, spec: dict[str, Any]) -> list[Finding]:
        value = spec.get("trigger_count")
        if isinstance(value, bool) or not isinstance(value, int) or value < self._min_triggers:
            return [
                _fail(
                    "L2.trigger_count",
                    "trigger_count",
                    "too few distinct trigger scenarios to justify a new artifact",
                    f">= {self._min_triggers}",
                    repr(value),
                )
            ]
        return []

    def _intent_findings(self, spec: dict[str, Any]) -> list[Finding]:
        intent = spec.get("intent")
        if not isinstance(intent, str) or not intent.strip():
            return [
                _fail(
                    "L2.intent_missing",
                    "intent",
                    "intent must state, in one specific sentence, why this artifact exists",
                    "a non-empty sentence",
                    repr(intent),
                )
            ]
        text = " ".join(intent.split())
        name = str(spec.get("name") or "").replace("-", " ").strip()
        restates_name = bool(name) and text.casefold() == name.casefold()
        if len(text.split()) < self._min_intent_words or restates_name:
            return [
                _fail(
                    "L2.intent_unspecific",
                    "intent",
                    "intent restates the name or is too short to be actionable",
                    f">= {self._min_intent_words} words, not a restatement of the name",
                    repr(text),
                )
            ]
        return []

    def _tier_findings(self, spec: dict[str, Any]) -> list[Finding]:
        tier = spec.get("tier")
        if tier not in self._tiers:
            return [
                _fail(
                    "L2.tier",
                    "tier",
                    "tier must be one the output template defines",
                    " | ".join(self._tiers),
                    repr(tier),
                )
            ]
        return []
