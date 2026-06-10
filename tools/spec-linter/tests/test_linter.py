"""Tests for the Gate A spec linter — one test per narrative point."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from spec_linter.linter import emit_json_schema, lint_dir, lint_spec
from spec_linter.verdict import Level

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


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


def _rules(verdict: Any) -> list[str]:
    return [f.rule for f in verdict.findings]


def test_valid_spec_passes(valid_spec: dict[str, Any]) -> None:
    verdict = lint_spec(valid_spec)
    assert verdict.level == Level.PASS
    assert verdict.findings == []


def test_missing_required_field_is_l1_fail(valid_spec: dict[str, Any]) -> None:
    del valid_spec["model"]
    verdict = lint_spec(valid_spec)
    assert verdict.level == Level.FAIL
    schema_findings = [f for f in verdict.findings if f.rule == "L1.schema"]
    assert any(f.field == "model" for f in schema_findings)


def test_v2_without_observability_is_l2_fail(valid_spec: dict[str, Any]) -> None:
    valid_spec["observability"] = None
    verdict = lint_spec(valid_spec)
    assert verdict.level == Level.FAIL
    assert "L2.maturity_observability" in _rules(verdict)


def test_v3_without_memory_and_recall_is_fail(valid_spec: dict[str, Any]) -> None:
    valid_spec["maturity"] = "V3"
    valid_spec["memory_backend"] = None
    valid_spec["recall_strategy"] = None
    verdict = lint_spec(valid_spec)
    assert verdict.level == Level.FAIL
    rules = _rules(verdict)
    assert "L2.maturity_memory_backend" in rules
    assert "L2.maturity_recall_strategy" in rules


def test_publish_without_security_review_is_fail(valid_spec: dict[str, Any]) -> None:
    valid_spec["publish"] = True
    valid_spec["security_review"] = False
    verdict = lint_spec(valid_spec)
    assert verdict.level == Level.FAIL
    assert "L2.publish_security_review" in _rules(verdict)


def test_requirement_without_deliverable_is_fail(valid_spec: dict[str, Any]) -> None:
    valid_spec["requirements"] = ["lint the diff", "publish results"]
    valid_spec["deliverables"] = ["lint the diff"]
    verdict = lint_spec(valid_spec)
    assert verdict.level == Level.FAIL
    findings = [f for f in verdict.findings if f.rule == "L3.requirement_without_deliverable"]
    assert len(findings) == 1
    assert "publish results" in findings[0].message


def test_duplicate_id_across_dir_is_fail(tmp_path: Path, valid_spec: dict[str, Any]) -> None:
    import yaml

    (tmp_path / "a.yaml").write_text(yaml.safe_dump(valid_spec))
    (tmp_path / "b.yaml").write_text(yaml.safe_dump(valid_spec))  # same id

    verdicts = lint_dir(tmp_path)
    assert set(verdicts) == {"a.yaml", "b.yaml"}
    for name in ("a.yaml", "b.yaml"):
        assert verdicts[name].level == Level.FAIL
        dupes = [f for f in verdicts[name].findings if f.rule == "L4.duplicate_id"]
        assert len(dupes) == 1
        assert "a.yaml" in dupes[0].found and "b.yaml" in dupes[0].found


def test_unknown_field_is_warn_only(valid_spec: dict[str, Any]) -> None:
    valid_spec["totally_made_up_key"] = 123
    verdict = lint_spec(valid_spec)
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
