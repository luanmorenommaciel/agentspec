"""Per-dimension measurement behavior over a parsed AgentSpec."""

from __future__ import annotations

import pytest

from spec_linter import AgentSpec

from spec_scorer import dimensions


def _spec(spec_dict: dict) -> AgentSpec:
    return AgentSpec.model_validate(spec_dict)


def test_completeness_full(valid_spec) -> None:
    d = dimensions.completeness(_spec(valid_spec))
    assert (d.numerator, d.denominator) == (6, 6)
    assert d.ratio == pytest.approx(1.0)


def test_completeness_partial(bare_v3_spec) -> None:
    d = dimensions.completeness(_spec(bare_v3_spec))
    # bare spec populates none of the 6 enrichment fields
    assert d.numerator == 0
    assert d.denominator == 6
    assert "missing" in d.detail


def test_maturity_conformance_complete_v2(valid_spec) -> None:
    d = dimensions.maturity_conformance(_spec(valid_spec))
    assert (d.numerator, d.denominator) == (3, 3)


def test_maturity_conformance_overclaim(bare_v3_spec) -> None:
    """The star dimension: declares V3, carries only V1 evidence -> 2/5."""
    d = dimensions.maturity_conformance(_spec(bare_v3_spec))
    assert d.denominator == 5
    assert d.numerator == 2
    assert d.ratio == pytest.approx(0.4)
    assert "V3" in d.detail


def test_mitigation_coverage_drops_inapplicable_security_review(valid_spec) -> None:
    # publish is False -> security_review is not applicable, denominator stays 3
    d = dimensions.mitigation_coverage(_spec(valid_spec))
    assert d.denominator == 3
    assert d.numerator == 3


def test_mitigation_coverage_counts_security_review_when_publishing(valid_spec) -> None:
    valid_spec["publish"] = True
    valid_spec["security_review"] = False
    d = dimensions.mitigation_coverage(_spec(valid_spec))
    assert d.denominator == 4  # security_review now applicable
    assert d.numerator == 3  # ...but absent
    assert "security_review" in d.detail


def test_risk_surface_polarity_and_points(valid_spec) -> None:
    valid_spec["output_contract"]["side_effects"] = {
        "files_written": True,
        "git_operations": ["commit", "push"],
        "external_apis": ["openrouter"],
    }
    valid_spec["tools"] = ["read_file", "write_file", "bash"]
    valid_spec["tier"] = "T3"
    d = dimensions.risk_surface(_spec(valid_spec))
    assert d.higher_is_better is False
    # 1 (write) + 2 (git) + 1 (api) + 3 (tools) + 2 (T3) = 9
    assert d.numerator == 9
    assert d.denominator == 12


def test_reference_integrity_flags_dangling(valid_spec) -> None:
    valid_spec["kb_domains"] = ["testing", "does-not-exist"]
    d = dimensions.reference_integrity(_spec(valid_spec), known_kb_domains={"testing", "python"})
    assert (d.numerator, d.denominator) == (1, 2)
    assert "does-not-exist" in d.detail


def test_actual_reuse_caps_at_target(valid_spec) -> None:
    d = dimensions.actual_reuse(_spec(valid_spec), inbound_references=10)
    assert d.numerator == d.denominator  # capped at the nominal target
    assert "10 inbound" in d.detail
