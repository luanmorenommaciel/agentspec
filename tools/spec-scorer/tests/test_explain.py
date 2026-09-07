"""`--explain` per-topic breakdown: CheckItem, render, CLI, and invariants."""

from __future__ import annotations

import yaml

from spec_linter import AgentSpec

from spec_scorer import AgentSpecScoringContract, CheckItem, dimensions, score
from spec_scorer.cli import main


def _spec(spec_dict: dict) -> AgentSpec:
    return AgentSpec.model_validate(spec_dict)


def test_checkitem_render_bool() -> None:
    assert CheckItem(label="tools_declared", contribution=1).render() == "    ✓ tools_declared"
    assert CheckItem(label="kb_domains_declared", contribution=0).render() == "    ✗ kb_domains_declared"


def test_checkitem_render_points_with_note() -> None:
    item = CheckItem(label="tier", contribution=2, kind="points", note="T3")
    assert item.render() == "    +2  tier (T3)"


def test_compact_render_unchanged_by_checks(valid_spec) -> None:
    """A dimension with checks still renders the terse detail line in compact
    mode — explain is opt-in, the default output is untouched."""
    d = dimensions.completeness(_spec(valid_spec))
    compact = d.render(explain=False)
    assert "✓" not in compact and "✗" not in compact
    # explain mode swaps the detail line for the per-topic checks
    explained = d.render(explain=True)
    assert "✓ kb_domains" in explained


def test_checklist_numerator_equals_sum_of_contributions(valid_spec) -> None:
    """The per-topic breakdown reconciles with the dimension ratio: for the
    boolean checklist dimensions, numerator == sum of check contributions."""
    for build in (
        dimensions.completeness,
        dimensions.convention_conformance,
        dimensions.mitigation_coverage,
        dimensions.maturity_conformance,
    ):
        d = build(_spec(valid_spec))
        assert d.numerator == sum(c.contribution for c in d.checks)


def test_risk_surface_checks_are_points(valid_spec) -> None:
    valid_spec["tier"] = "T3"
    d = dimensions.risk_surface(_spec(valid_spec))
    assert all(c.kind == "points" for c in d.checks)
    tier_check = next(c for c in d.checks if c.label == "tier")
    assert tier_check.contribution == 2 and tier_check.note == "T3"


def test_behavioral_checks_cover_four_categories() -> None:
    from spec_linter import Finding, Level, Verdict

    from spec_scorer.behavioral import fold_behavioral

    verdict = Verdict.from_findings(
        [Finding(level=Level.WARN, rule="B1.vagueness", message="v")]
    )
    d = fold_behavioral(verdict)[0]
    assert len(d.checks) == 4
    b1 = next(c for c in d.checks if c.label.startswith("B1"))
    assert b1.contribution == 0 and "raised ×1" in b1.note
    b2 = next(c for c in d.checks if c.label.startswith("B2"))
    assert b2.contribution == 1  # absent category is clean


def test_scorecard_render_explain_includes_topics(valid_spec) -> None:
    card = score(valid_spec, AgentSpecScoringContract())
    explained = card.render(explain=True)
    assert "✓ tools_declared" in explained
    assert "+1  tier" in explained
    # compact default omits them
    assert "✓ tools_declared" not in card.render(explain=False)


def test_cli_explain_flag(tmp_path, valid_spec, capsys) -> None:
    f = tmp_path / "agent.yaml"
    f.write_text(yaml.safe_dump(valid_spec), encoding="utf-8")
    assert main([str(f), "--explain"]) == 0
    out = capsys.readouterr().out
    assert "✓ tools_declared" in out
    assert "maturity_conformance" in out


def test_cli_without_explain_is_compact(tmp_path, valid_spec, capsys) -> None:
    f = tmp_path / "agent.yaml"
    f.write_text(yaml.safe_dump(valid_spec), encoding="utf-8")
    assert main([str(f)]) == 0
    out = capsys.readouterr().out
    assert "✓" not in out  # no per-topic marks in the compact default
