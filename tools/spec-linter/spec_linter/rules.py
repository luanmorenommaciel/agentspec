"""Governance / consistency / identity checks (L2-L4).

These run *after* L1 schema validation has produced a valid `AgentSpec`. They are
plain functions returning `list[Finding]` rather than model_validators, so a spec
that is schema-valid but governance-invalid yields clean L2 findings instead of an
L1 ValidationError. L1 (Pydantic) and L2 (this module) stay cleanly separated.
"""

from __future__ import annotations

from .models import AgentSpec
from .verdict import Finding, Level

# Known field names, used to flag unknown/extra keys as WARN.
KNOWN_FIELDS = frozenset(AgentSpec.model_fields)


def unknown_field_findings(spec: AgentSpec) -> list[Finding]:
    """WARN on each unknown key collected by `extra='allow'` (via model_extra)."""
    extra = spec.model_extra or {}
    return [
        Finding(
            level=Level.WARN,
            rule="L1.unknown_field",
            field=key,
            message=f"unknown field '{key}' is not part of the agent spec",
        )
        for key in extra
    ]


def l2_governance_findings(spec: AgentSpec) -> list[Finding]:
    """L2 — cross-field governance / policy rules."""
    findings: list[Finding] = []

    if len(spec.stop_conditions) < 1:
        findings.append(
            Finding(
                level=Level.FAIL,
                rule="L2.stop_conditions_required",
                field="stop_conditions",
                message=f"maturity {spec.maturity} requires at least one stop condition",
                expected=">= 1 item",
                found=f"{len(spec.stop_conditions)} items",
            )
        )
    if len(spec.escalation_rules) < 1:
        findings.append(
            Finding(
                level=Level.FAIL,
                rule="L2.escalation_rules_required",
                field="escalation_rules",
                message=f"maturity {spec.maturity} requires at least one escalation rule",
                expected=">= 1 item",
                found=f"{len(spec.escalation_rules)} items",
            )
        )

    if spec.maturity in ("V2", "V3") and spec.observability is None:
        findings.append(
            Finding(
                level=Level.FAIL,
                rule="L2.maturity_observability",
                field="observability",
                message=f"maturity {spec.maturity} requires an observability block",
                expected="observability block present",
                found="null",
            )
        )

    if spec.maturity == "V3":
        if spec.memory_backend is None:
            findings.append(
                Finding(
                    level=Level.FAIL,
                    rule="L2.maturity_memory_backend",
                    field="memory_backend",
                    message="maturity V3 requires memory_backend to be set",
                    expected="one of kv|vector|graph|none",
                    found="null",
                )
            )
        if spec.recall_strategy is None:
            findings.append(
                Finding(
                    level=Level.FAIL,
                    rule="L2.maturity_recall_strategy",
                    field="recall_strategy",
                    message="maturity V3 requires recall_strategy to be set",
                    expected="one of per-session|per-user|global",
                    found="null",
                )
            )

    if spec.publish and not spec.security_review:
        findings.append(
            Finding(
                level=Level.FAIL,
                rule="L2.publish_security_review",
                field="security_review",
                message="publish=true requires security_review=true",
                expected="true",
                found="false",
            )
        )

    return findings


def l3_consistency_findings(spec: AgentSpec) -> list[Finding]:
    """L3 — every requirement must have a matching deliverable (exact string)."""
    deliverables = set(spec.deliverables)
    findings: list[Finding] = []
    for req in spec.requirements:
        if req not in deliverables:
            findings.append(
                Finding(
                    level=Level.FAIL,
                    rule="L3.requirement_without_deliverable",
                    field="requirements",
                    message=f"requirement '{req}' has no corresponding deliverable",
                    expected=f"a deliverable matching '{req}'",
                    found="no match",
                )
            )
    return findings


def l4_identity_findings(ids_by_source: dict[str, list[str]]) -> list[Finding]:
    """L4 — duplicate `id` across files in a directory lint.

    `ids_by_source` maps spec id -> list of source file names that declared it.
    Only ids claimed by 2+ files produce a finding.
    """
    findings: list[Finding] = []
    for spec_id, sources in ids_by_source.items():
        if len(sources) > 1:
            findings.append(
                Finding(
                    level=Level.FAIL,
                    rule="L4.duplicate_id",
                    field="id",
                    message=f"id '{spec_id}' is declared by multiple specs",
                    expected="unique id per spec",
                    found=", ".join(sorted(sources)),
                )
            )
    return findings
