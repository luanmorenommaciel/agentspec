"""Agent-spec REFERENCE contract (authored as code).

REFERENCE IMPLEMENTATION — pending the canonical agent-spec schema, owned
upstream. Packages the Pydantic model + governance rules as a Contract so the
engine can validate agent specs without knowing they are specs. The same
Pydantic model also emits the spec JSON Schema (emit_json_schema), which is a
CONTRACT capability, not an engine one.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from .. import rules
from ..models import AgentSpec
from ..verdict import Finding


class AgentSpecContract:
    name = "agent-spec"

    def parse(self, artifact: Any) -> AgentSpec:
        """Validate the artifact into an `AgentSpec`, or raise on schema failure.

        Per the Contract protocol, an unparseable artifact is signalled by
        raising: the engine converts that into a single `agent-spec.unparseable`
        FAIL finding. The raised message preserves per-field detail so no
        schema information is lost.
        """
        try:
            return AgentSpec.model_validate(artifact)
        except ValidationError as exc:
            raise ValueError(_schema_message(exc)) from exc

    def check(self, parsed: AgentSpec) -> list[Finding]:
        """Run L1-unknown / L2 / L3 checks on a successfully parsed spec."""
        findings = rules.unknown_field_findings(parsed)
        findings += rules.l2_governance_findings(parsed)
        findings += rules.l3_consistency_findings(parsed)
        return findings


def emit_json_schema() -> dict[str, Any]:
    """The reference contract's Pydantic model emits the spec JSON Schema."""
    return AgentSpec.model_json_schema()


def _schema_message(error: ValidationError) -> str:
    parts = []
    for err in error.errors():
        field = ".".join(str(part) for part in err["loc"]) or "<root>"
        parts.append(f"{field}: {err['msg']} [{err['type']}]")
    return "schema validation failed — " + "; ".join(parts)
