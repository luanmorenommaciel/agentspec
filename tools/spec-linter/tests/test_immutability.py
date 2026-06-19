"""Frozen value objects: Verdict, Finding, and AgentSpec reject mutation."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from spec_linter.models import AgentSpec
from spec_linter.verdict import Finding, Level, Verdict


def test_finding_is_frozen() -> None:
    finding = Finding(level=Level.WARN, rule="L1.unknown_field", message="x")
    with pytest.raises(ValidationError):
        finding.rule = "mutated"


def test_verdict_is_frozen() -> None:
    verdict = Verdict.from_findings([])
    with pytest.raises(ValidationError):
        verdict.level = Level.FAIL


def test_verdict_from_findings_builds_new_instance() -> None:
    finding = Finding(level=Level.FAIL, rule="r", message="m")
    verdict = Verdict.from_findings([finding])
    assert verdict.level == Level.FAIL
    assert verdict.findings == [finding]


def test_agent_spec_is_frozen(valid_spec: dict[str, Any]) -> None:
    spec = AgentSpec.model_validate(valid_spec)
    with pytest.raises(ValidationError):
        spec.id = "mutated-id"
