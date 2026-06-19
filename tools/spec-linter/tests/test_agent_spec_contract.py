"""Tests for the agent-spec reference contract, run through `engine.lint`.

One test per documented spec-level behavior: L1 schema failures, L2 governance
rules, L3 requirement/deliverable consistency, unknown-field WARNs, and the
JSON Schema emission owned by the contract.
"""

from __future__ import annotations

from typing import Any

from spec_linter.contracts.agent_spec import AgentSpecContract, emit_json_schema
from spec_linter.engine import lint
from spec_linter.verdict import Level, Verdict

_CONTRACT = AgentSpecContract()


def _lint(spec: dict[str, Any]) -> Verdict:
    return lint(spec, _CONTRACT)


def _rules(verdict: Verdict) -> list[str]:
    return [f.rule for f in verdict.findings]


def test_valid_spec_passes(valid_spec: dict[str, Any]) -> None:
    verdict = _lint(valid_spec)
    assert verdict.level == Level.PASS
    assert verdict.findings == []


def test_missing_required_field_is_unparseable_fail(valid_spec: dict[str, Any]) -> None:
    del valid_spec["model"]
    verdict = _lint(valid_spec)
    assert verdict.level == Level.FAIL
    assert len(verdict.findings) == 1
    finding = verdict.findings[0]
    assert finding.rule == "agent-spec.unparseable"
    assert "model" in finding.message


def test_v2_without_observability_is_l2_fail(valid_spec: dict[str, Any]) -> None:
    valid_spec["observability"] = None
    verdict = _lint(valid_spec)
    assert verdict.level == Level.FAIL
    assert "L2.maturity_observability" in _rules(verdict)


def test_v3_without_memory_and_recall_is_fail(valid_spec: dict[str, Any]) -> None:
    valid_spec["maturity"] = "V3"
    valid_spec["memory_backend"] = None
    valid_spec["recall_strategy"] = None
    verdict = _lint(valid_spec)
    assert verdict.level == Level.FAIL
    rules = _rules(verdict)
    assert "L2.maturity_memory_backend" in rules
    assert "L2.maturity_recall_strategy" in rules


def test_publish_without_security_review_is_fail(valid_spec: dict[str, Any]) -> None:
    valid_spec["publish"] = True
    valid_spec["security_review"] = False
    verdict = _lint(valid_spec)
    assert verdict.level == Level.FAIL
    assert "L2.publish_security_review" in _rules(verdict)


def test_requirement_without_deliverable_is_fail(valid_spec: dict[str, Any]) -> None:
    valid_spec["requirements"] = ["lint the diff", "publish results"]
    valid_spec["deliverables"] = ["lint the diff"]
    verdict = _lint(valid_spec)
    assert verdict.level == Level.FAIL
    findings = [f for f in verdict.findings if f.rule == "L3.requirement_without_deliverable"]
    assert len(findings) == 1
    assert "publish results" in findings[0].message


def test_unknown_field_is_warn_only(valid_spec: dict[str, Any]) -> None:
    valid_spec["totally_made_up_key"] = 123
    verdict = _lint(valid_spec)
    assert verdict.level == Level.WARN
    unknowns = [f for f in verdict.findings if f.rule == "L1.unknown_field"]
    assert len(unknowns) == 1
    assert unknowns[0].field == "totally_made_up_key"
    assert unknowns[0].level == Level.WARN


def test_emit_json_schema_has_expected_keys() -> None:
    schema = emit_json_schema()
    assert "properties" in schema
    assert "output_contract" in schema["properties"]
    assert "maturity" in schema["properties"]
