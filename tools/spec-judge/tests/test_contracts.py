"""SpecConformanceContract: parsing/normalization and the rendered contract summary."""

from __future__ import annotations

import pytest

from spec_judge.contracts import EvalSubject, SpecConformanceContract, split_frontmatter


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


def test_contract_summary_projects_stop_conditions_and_observability(source_spec) -> None:
    # A body that never stops despite a declared stop condition is a behavioral defect
    # the panel can only see if the contract summary actually surfaces it.
    summary = SpecConformanceContract(source_spec).parse("x").contract_summary
    assert "stop when the diff exceeds 5000 lines" in summary
    assert "confidence_scoring=True" in summary
    assert "sources_attribution=True" in summary


def test_split_frontmatter_survives_an_indented_hrule_in_a_block_scalar() -> None:
    # A YAML block scalar (`description: |`) may contain a line that merely looks like
    # an hrule when indented; only a column-0 `---` is a real fence.
    text = (
        "---\n"
        "id: report-writer\n"
        "description: |\n"
        "  line one\n"
        "  ---\n"
        "  line two\n"
        "output_contract:\n"
        "  format: structured-report\n"
        "---\n"
        "The real body.\n"
    )
    spec, body = split_frontmatter(text)
    assert spec is not None
    assert spec["output_contract"] == {"format": "structured-report"}
    assert spec["description"] == "line one\n---\nline two\n"
    assert body == "The real body.\n"


def test_split_frontmatter_leaves_a_body_hrule_untouched() -> None:
    # A `---` hrule in the body, AFTER the real closing fence, must stay in the body —
    # it must not be mistaken for another frontmatter boundary.
    text = "---\nid: x\n---\nBefore the rule.\n---\nAfter the rule.\n"
    spec, body = split_frontmatter(text)
    assert spec == {"id": "x"}
    assert body == "Before the rule.\n---\nAfter the rule.\n"
