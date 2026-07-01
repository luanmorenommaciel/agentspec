"""SpecConformanceContract: parsing/normalization and the rendered contract summary."""

from __future__ import annotations

import pytest

from spec_judge.contracts import EvalSubject, SpecConformanceContract


def test_parse_binds_spec_and_keeps_text(source_spec) -> None:
    subject = SpecConformanceContract(source_spec).parse("the body")
    assert isinstance(subject, EvalSubject)
    assert subject.artifact_text == "the body"
    assert subject.source_spec_id == "code-reviewer"


def test_parse_mapping_artifact_renders_json(source_spec) -> None:
    subject = SpecConformanceContract(source_spec).parse({"summary": "s", "findings": []})
    assert '"summary"' in subject.artifact_text


def test_empty_artifact_raises(source_spec) -> None:
    with pytest.raises(ValueError):
        SpecConformanceContract(source_spec).parse("   ")


def test_rubric_probes_the_four_categories(source_spec) -> None:
    assert SpecConformanceContract(source_spec).rubric().categories == ("B1", "B2", "B3", "B4")


def test_contract_summary_projects_output_contract_and_intent(source_spec) -> None:
    summary = SpecConformanceContract(source_spec).parse("x").contract_summary
    assert "output_contract.required_fields: summary, findings" in summary
    assert "files_written=False" in summary
    assert "description (intent): Reviews Python diffs against house standards." in summary
