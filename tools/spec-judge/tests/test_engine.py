"""Engine: the happy path, the unparseable path, and the default tier."""

from __future__ import annotations

from _helpers import evaluator_from
from spec_linter import Level

from spec_judge.contracts import SpecConformanceContract
from spec_judge.engine import judge
from spec_judge.panel import Panel, Seat


def test_clean_artifact_passes(source_spec) -> None:
    panel = Panel.standard(evaluator=evaluator_from({}))  # every seat clean
    verdict = judge("a body that honors the contract", SpecConformanceContract(source_spec), panel)
    assert verdict.level == Level.PASS
    assert verdict.findings == []


def test_unparseable_artifact_is_single_fail(source_spec) -> None:
    verdict = judge(
        "   ", SpecConformanceContract(source_spec), Panel.smoke(evaluator=evaluator_from({}))
    )
    assert verdict.level == Level.FAIL
    assert len(verdict.findings) == 1
    assert verdict.findings[0].rule == "spec-conformance:code-reviewer.unparseable"


def test_panel_none_defaults_to_standard(source_spec, monkeypatch) -> None:
    # panel=None must build the standard tier. Stub Panel.standard so no real evaluator
    # (and no network) is constructed.
    import spec_judge.engine as engine_module

    built: dict[str, str] = {}

    def fake_standard():
        built["tier"] = "standard"
        return Panel(
            "standard",
            [Seat(role="fault-seeker"), Seat(role="arbiter")],
            evaluator=evaluator_from({}),
        )

    monkeypatch.setattr(engine_module.Panel, "standard", staticmethod(fake_standard))
    verdict = judge("body", SpecConformanceContract(source_spec))
    assert built.get("tier") == "standard"
    assert verdict.level == Level.PASS
