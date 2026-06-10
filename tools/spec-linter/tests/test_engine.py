"""Tests for the engine (pure mechanism) and the three contract sources."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from spec_linter.contracts.agent_spec import AgentSpecContract, emit_json_schema
from spec_linter.contracts.instance import InstanceContract
from spec_linter.contracts.sdd_phase import SddPhaseContract
from spec_linter.engine import lint
from spec_linter.protocol import Contract
from spec_linter.verdict import Finding, Level


@pytest.fixture
def valid_spec() -> dict[str, Any]:
    """A minimal, fully governance-compliant V2 spec as a fresh dict per test."""
    return copy.deepcopy(
        {
            "id": "code-reviewer",
            "name": "Code Reviewer",
            "description": "Reviews diffs.",
            "model": "claude-opus-4",
            "tools": ["read_file"],
            "maturity": "V2",
            "tier": "T2",
            "output_contract": {
                "format": "structured-report",
                "required_fields": ["summary"],
                "side_effects": {
                    "files_written": False,
                    "git_operations": ["none"],
                    "external_apis": [],
                },
            },
            "stop_conditions": ["no diff"],
            "escalation_rules": ["escalate on security change"],
            "observability": {"confidence_scoring": True, "sources_attribution": True},
            "memory_backend": "none",
            "recall_strategy": "per-session",
            "requirements": ["lint the diff"],
            "deliverables": ["lint the diff"],
        }
    )


def test_engine_runs_contract_and_assembles_verdict(valid_spec: dict[str, Any]) -> None:
    verdict = lint(valid_spec, AgentSpecContract())
    assert verdict.level == Level.PASS
    assert verdict.findings == []


def test_engine_agent_spec_schema_fail(valid_spec: dict[str, Any]) -> None:
    del valid_spec["model"]
    verdict = lint(valid_spec, AgentSpecContract())
    assert verdict.level == Level.FAIL
    schema_findings = [f for f in verdict.findings if f.rule == "L1.schema"]
    assert any(f.field == "model" for f in schema_findings)


def test_engine_unparseable_artifact() -> None:
    class ExplodingContract:
        name = "exploding"

        def parse(self, artifact: Any) -> Any:
            raise ValueError("cannot parse this artifact")

        def check(self, parsed: Any) -> list[Finding]:
            return []

    verdict = lint("anything", ExplodingContract())
    assert verdict.level == Level.FAIL
    assert len(verdict.findings) == 1
    finding = verdict.findings[0]
    assert finding.rule == "exploding.unparseable"
    assert "cannot parse this artifact" in finding.message


def test_sdd_phase_contract_missing_section() -> None:
    contract = SddPhaseContract("define", ["Problem Statement", "User Stories"])
    document = "# DEFINE\n\n## Problem Statement\n\nSome text.\n"
    verdict = lint(document, contract)
    assert verdict.level == Level.FAIL
    missing = [f for f in verdict.findings if f.rule == "L2.required_section"]
    assert len(missing) == 1
    assert missing[0].field == "User Stories"


def test_sdd_phase_contract_all_present() -> None:
    contract = SddPhaseContract("define", ["Problem Statement", "User Stories"])
    document = "# DEFINE\n\n## Problem statement!\n\nText.\n\n### user stories\n\nMore text.\n"
    verdict = lint(document, contract)
    assert verdict.level == Level.PASS
    assert verdict.findings == []


def test_instance_contract_missing_declared_field(valid_spec: dict[str, Any]) -> None:
    verdict = lint({}, InstanceContract(valid_spec))
    assert verdict.level == Level.FAIL
    findings = [f for f in verdict.findings if f.rule == "L3.missing_declared_field"]
    assert len(findings) == 1
    assert findings[0].field == "summary"


def test_emit_json_schema_lives_on_contract() -> None:
    schema = emit_json_schema()
    assert "output_contract" in schema["properties"]


def test_contract_protocol_runtime_checkable() -> None:
    assert isinstance(AgentSpecContract(), Contract)
    assert isinstance(SddPhaseContract("define", ["Problem Statement"]), Contract)
