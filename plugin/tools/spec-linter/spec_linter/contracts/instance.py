"""Instance-derived contract (the artifact's own declaration becomes the rule).

A spec instance declares its own `output_contract.required_fields`; this turns
that declaration into a Contract and checks a produced artifact mapping against
it. Minimal by design.
"""

from __future__ import annotations

from typing import Any

from ..verdict import Finding, Level


class InstanceContract:
    def __init__(self, spec: dict[str, Any]) -> None:
        self.name = f"instance:{spec.get('id', '?')}"
        self._required = list((spec.get("output_contract") or {}).get("required_fields", []))

    def parse(self, artifact: dict[str, Any]) -> dict[str, Any]:
        return artifact

    def check(self, artifact: dict[str, Any]) -> list[Finding]:
        return [
            Finding(
                level=Level.FAIL,
                rule="L3.missing_declared_field",
                field=field,
                message=f"declared required_field '{field}' absent from artifact",
                expected="present",
                found="absent",
            )
            for field in self._required
            if field not in artifact
        ]
