"""Agent-spec REFERENCE contract (authored as code).

REFERENCE IMPLEMENTATION — pending pod D1's canonical agent-spec schema. This
repackages the existing Pydantic model + governance rules as a Contract so the
engine can validate agent specs without knowing they are specs. The same
Pydantic model still emits the spec JSON Schema (emit_json_schema), which is a
CONTRACT capability, not an engine one.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from .. import rules
from ..models import AgentSpec
from ..verdict import Finding, Level


class AgentSpecContract:
    name = "agent-spec"

    def parse(self, artifact: Any) -> AgentSpec | list[Finding]:
        try:
            return AgentSpec.model_validate(artifact)
        except ValidationError as exc:
            return _schema_findings(exc)  # parse "succeeds" into findings; check() forwards them

    def check(self, parsed: AgentSpec | list[Finding]) -> list[Finding]:
        if isinstance(parsed, list):  # schema-invalid: forward L1.schema FAILs as-is
            return parsed
        findings = rules.unknown_field_findings(parsed)
        findings += rules.l2_governance_findings(parsed)
        findings += rules.l3_consistency_findings(parsed)
        return findings


def emit_json_schema() -> dict[str, Any]:
    """The reference contract's Pydantic model emits the spec JSON Schema."""
    return AgentSpec.model_json_schema()


def _schema_findings(error: ValidationError) -> list[Finding]:
    findings: list[Finding] = []
    for err in error.errors():
        field = ".".join(str(part) for part in err["loc"]) or None
        findings.append(
            Finding(
                level=Level.FAIL,
                rule="L1.schema",
                field=field,
                message=err["msg"],
                found=err["type"],
            )
        )
    return findings
