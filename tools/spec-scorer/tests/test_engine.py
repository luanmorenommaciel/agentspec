"""Engine orchestration: determinism, provenance, evidence availability."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from spec_linter import AgentSpec

from spec_scorer import AgentSpecScoringContract, score


def test_scores_are_deterministic(valid_spec) -> None:
    """Same artifact + contract -> identical dimensions across runs."""
    c = AgentSpecScoringContract()
    a = score(valid_spec, c)
    b = score(valid_spec, c)
    assert a.dimensions == b.dimensions


def test_full_scorecard_identical_with_pinned_clock(valid_spec) -> None:
    """With `now` injected, even the provenance timestamp matches -> full equality."""
    c = AgentSpecScoringContract()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert score(valid_spec, c, now=now) == score(valid_spec, c, now=now)


def test_no_verdict_means_no_behavioral_family(valid_spec) -> None:
    card = score(valid_spec, AgentSpecScoringContract())
    assert "Behavioral Quality" not in card.by_family()
    assert "judger" not in card.evidence_sources
    assert card.judger_tier is None


def test_reference_integrity_absent_without_kb_facts(valid_spec) -> None:
    card = score(valid_spec, AgentSpecScoringContract())
    dims = {d.dimension for d in card.dimensions}
    assert "reference_integrity" not in dims
    assert "kb-index" not in card.evidence_sources


def test_reference_integrity_present_with_kb_facts(valid_spec) -> None:
    card = score(valid_spec, AgentSpecScoringContract(known_kb_domains={"testing"}))
    dims = {d.dimension for d in card.dimensions}
    assert "reference_integrity" in dims
    assert "kb-index" in card.evidence_sources


def test_actual_reuse_uses_injected_inbound(valid_spec) -> None:
    card = score(
        valid_spec, AgentSpecScoringContract(inbound_references={"code-reviewer": 2})
    )
    reuse = next(d for d in card.dimensions if d.dimension == "actual_reuse")
    assert "2 inbound" in reuse.detail
    assert "repo-graph" in card.evidence_sources


def test_contract_version_stamped(valid_spec) -> None:
    card = score(valid_spec, AgentSpecScoringContract())
    assert card.contract_version == "0.1.0"


def test_contract_name_stamped(valid_spec) -> None:
    """Provenance carries the contract's identity, not just its version — two
    contracts sharing a version string are still distinguishable."""
    card = score(valid_spec, AgentSpecScoringContract())
    assert card.contract_name == "agent-spec"
    assert "agent-spec 0.1.0" in card.render()


def test_behavioral_family_present_with_verdict(valid_spec) -> None:
    from spec_linter import Finding, Level, Verdict

    verdict = Verdict.from_findings(
        [Finding(level=Level.WARN, rule="B1.vagueness", message="vague")]
    )
    card = score(
        valid_spec,
        AgentSpecScoringContract(),
        verdict=verdict,
        judger_tier="standard",
    )
    assert "Behavioral Quality" in card.by_family()
    assert "judger" in card.evidence_sources
    assert card.judger_tier == "standard"


def test_unparseable_artifact_raises(valid_spec) -> None:
    """The Scorer has nothing to measure on an unparseable artifact -> raise,
    not a low score. The CLI turns this into exit 2."""
    del valid_spec["maturity"]  # required field
    with pytest.raises(Exception):
        score(valid_spec, AgentSpecScoringContract())
