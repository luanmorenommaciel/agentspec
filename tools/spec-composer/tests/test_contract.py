"""Tests for the pipeline contract — the Composer's own dogfooded policy schema."""

from __future__ import annotations

from typing import Any

import pytest
import yaml
from conftest import EXAMPLES
from pydantic import ValidationError
from spec_linter import Contract, Level, lint

from spec_composer.contract import JUDGE_TIERS, PipelineContract, PipelineSpec, Stage


def _load(name: str) -> dict[str, Any]:
    return yaml.safe_load((EXAMPLES / name).read_text(encoding="utf-8"))


def test_shipped_pipeline_has_no_findings(shipped_document: dict[str, Any]) -> None:
    verdict = lint(shipped_document, PipelineContract())
    assert verdict.level == Level.PASS
    assert verdict.findings == []


def test_judge_before_gate_fails() -> None:
    verdict = lint(_load("invalid_judge_before_gate.yaml"), PipelineContract())
    assert verdict.level == Level.FAIL
    assert any(finding.rule == "P2.judge_after_gates" for finding in verdict.findings)


def test_ungated_emit_fails() -> None:
    verdict = lint(_load("invalid_ungated_emit.yaml"), PipelineContract())
    assert verdict.level == Level.FAIL
    assert any(finding.rule == "P2.emit_gated" for finding in verdict.findings)


def test_emit_before_gate_fails() -> None:
    document = {
        "pipeline": "emit-before-gate",
        "version": 1,
        "max_attempts": 1,
        "stages": [
            {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
            {"id": "gate-a", "kind": "lint", "input_contract": "creation-spec"},
            {
                "id": "generate-agent",
                "kind": "generate",
                "input_contract": "creation-spec",
                "output_contract": "agent-spec",
            },
            {"id": "emit-agent", "kind": "emit"},
        ],
    }
    verdict = lint(document, PipelineContract())
    assert verdict.level == Level.FAIL
    assert any(finding.rule == "P2.emit_gated" for finding in verdict.findings)


def test_emit_not_last_fails() -> None:
    verdict = lint(_load("invalid_emit_not_last.yaml"), PipelineContract())
    assert verdict.level == Level.FAIL
    rules = {finding.rule for finding in verdict.findings}
    assert {"P2.emit_last", "P2.emit_gated"} <= rules


def test_judge_without_any_gate_fails() -> None:
    document = {
        "pipeline": "judge-without-subject",
        "version": 1,
        "max_attempts": 1,
        "stages": [{"id": "judge-only", "kind": "judge", "judge_tier": "standard"}],
    }
    verdict = lint(document, PipelineContract())
    assert verdict.level == Level.FAIL
    assert any(finding.rule == "P2.judge_without_subject" for finding in verdict.findings)


def test_multi_cycle_pipeline_passes() -> None:
    """The ordering rules are subject-aware: a judge stage may precede a later
    lint stage and still be legal, as long as its own subject was gated."""
    verdict = lint(_load("multi_cycle.yaml"), PipelineContract())
    assert verdict.level == Level.PASS
    assert not any(finding.level == Level.FAIL for finding in verdict.findings)


_RULE_CASES = (
    pytest.param(
        {
            "pipeline": "p",
            "max_attempts": 1,
            "stages": [{"id": "create-spec", "kind": "create", "output_contract": "creation-spec"}],
        },
        "P1.missing_field",
        Level.FAIL,
        id="P1.missing_field",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 0,
            "stages": [{"id": "create-spec", "kind": "create", "output_contract": "creation-spec"}],
        },
        "P1.max_attempts",
        Level.FAIL,
        id="P1.max_attempts",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [{"id": "mystery", "kind": "mystery-kind"}],
        },
        "P1.unknown_kind",
        Level.FAIL,
        id="P1.unknown_kind",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [
                {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
                {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
            ],
        },
        "P1.duplicate_stage_id",
        Level.FAIL,
        id="P1.duplicate_stage_id",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [
                {
                    "id": "create-spec",
                    "kind": "create",
                    "output_contract": "creation-spec",
                    "mystery": "x",
                }
            ],
        },
        "P1.unknown_field",
        Level.WARN,
        id="P1.unknown_field",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [{"id": "judge-only", "kind": "judge", "judge_tier": "standard"}],
        },
        "P2.judge_without_subject",
        Level.FAIL,
        id="P2.judge_without_subject",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [
                {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
                {"id": "judge-early", "kind": "judge", "judge_tier": "standard"},
            ],
        },
        "P2.judge_after_gates",
        Level.FAIL,
        id="P2.judge_after_gates",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [
                {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
                {
                    "id": "generate-agent",
                    "kind": "generate",
                    "input_contract": "creation-spec",
                    "output_contract": "agent-spec",
                },
            ],
        },
        "P2.generate_gated",
        Level.FAIL,
        id="P2.generate_gated",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [
                {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
                {"id": "emit-agent", "kind": "emit"},
            ],
        },
        "P2.emit_gated",
        Level.FAIL,
        id="P2.emit_gated",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [
                {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
                {"id": "gate-a", "kind": "lint", "input_contract": "creation-spec"},
                {"id": "emit-agent", "kind": "emit"},
                {"id": "gate-b", "kind": "lint"},
            ],
        },
        "P2.emit_last",
        Level.FAIL,
        id="P2.emit_last",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [{"id": "gate-a", "kind": "lint", "input_contract": "creation-spec"}],
        },
        "P3.stage_io_chain",
        Level.FAIL,
        id="P3.stage_io_chain",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [
                {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
                {"id": "gate-a", "kind": "lint", "input_contract": "creation-spec"},
                {"id": "judge-stage", "kind": "judge", "judge_tier": "bogus-tier"},
            ],
        },
        "P3.judge_tier",
        Level.FAIL,
        id="P3.judge_tier",
    ),
    pytest.param(
        {
            "pipeline": "p",
            "version": 1,
            "max_attempts": 1,
            "stages": [
                {"id": "create-spec", "kind": "create", "output_contract": "mystery-contract"}
            ],
        },
        "P3.dangling_reference",
        Level.WARN,
        id="P3.dangling_reference",
    ),
)


@pytest.mark.parametrize(("document", "rule", "level"), _RULE_CASES)
def test_rule_severities(document: dict[str, Any], rule: str, level: Level) -> None:
    """Each of the thirteen contract rules must fire alone, at its declared
    severity, from a document engineered to trip exactly that one rule."""
    verdict = lint(document, PipelineContract())
    assert len(verdict.findings) == 1
    finding = verdict.findings[0]
    assert finding.rule == rule
    assert finding.level == level


def test_pipeline_contract_reports_unparseable_artifact() -> None:
    verdict = lint([], PipelineContract())
    assert verdict.level == Level.FAIL
    assert len(verdict.findings) == 1
    assert verdict.findings[0].rule == "pipeline-contract.unparseable"


def test_max_attempts_rejects_bool() -> None:
    document = {
        "pipeline": "p",
        "version": 1,
        "max_attempts": True,
        "stages": [{"id": "create-spec", "kind": "create", "output_contract": "creation-spec"}],
    }
    verdict = lint(document, PipelineContract())
    assert verdict.level == Level.FAIL
    assert any(finding.rule == "P1.max_attempts" for finding in verdict.findings)


def test_judge_tiers_match_spec_judge_panel() -> None:
    import spec_judge.panel

    assert JUDGE_TIERS == spec_judge.panel.TIERS


def test_pipeline_contract_satisfies_contract_protocol() -> None:
    assert isinstance(PipelineContract(), Contract)


def test_pipeline_spec_from_mapping_builds_frozen_strict_view(
    shipped_document: dict[str, Any],
) -> None:
    spec = PipelineSpec.from_mapping(shipped_document)
    assert spec.pipeline == "agent-creation"
    assert all(isinstance(stage, Stage) for stage in spec.stages)
    with pytest.raises(ValidationError):
        spec.max_attempts = 99
