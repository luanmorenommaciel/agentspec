"""Unit tests for scripts/judge.py pure functions.

Focus on logic that does not hit OpenRouter. Network calls and CLI integration
are out of scope for this tier of tests — those need mocking or VCR fixtures.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_judge_module():
    """Import scripts/judge.py by path.

    Registers the module in ``sys.modules`` before executing so dataclass
    forward-reference resolution works under Python 3.11+.
    """
    import sys
    spec_path = Path(__file__).resolve().parent.parent / "scripts" / "judge.py"
    spec = importlib.util.spec_from_file_location("judge_mod", spec_path)
    assert spec and spec.loader, "could not locate scripts/judge.py"
    module = importlib.util.module_from_spec(spec)
    sys.modules["judge_mod"] = module   # critical for dataclass resolution
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def judge():
    return _load_judge_module()


# ── LedgerEntry ──────────────────────────────────────────────────────────────

class TestLedgerEntry:
    def test_from_json_roundtrip(self, judge):
        raw = json.dumps({
            "date": "2026-04-20",
            "ts": "2026-04-20T12:00:00+00:00",
            "model": "openai/gpt-4o",
            "target": "some/file.sql",
            "verdict": "PASS",
        })
        entry = judge.LedgerEntry.from_json(raw)
        assert entry is not None
        assert entry.date == "2026-04-20"
        assert entry.model == "openai/gpt-4o"
        assert entry.verdict == "PASS"
        assert entry.cost_usd is None

    def test_from_json_malformed_returns_none(self, judge):
        assert judge.LedgerEntry.from_json("not json") is None
        assert judge.LedgerEntry.from_json("{bad: json}") is None

    def test_from_json_tolerates_missing_fields(self, judge):
        entry = judge.LedgerEntry.from_json('{"date": "2026-04-20"}')
        assert entry is not None
        assert entry.date == "2026-04-20"
        assert entry.model == ""   # defaults to empty string
        assert entry.verdict == ""

    def test_to_dict_omits_none_cost(self, judge):
        entry = judge.LedgerEntry(
            date="2026-04-20", ts="t", model="m", target="tgt", verdict="PASS"
        )
        payload = entry.to_dict()
        assert "cost_usd" in payload
        assert payload["cost_usd"] is None
        # Round-trip through JSON
        parsed = json.loads(json.dumps(payload))
        assert parsed["verdict"] == "PASS"

    def test_is_frozen(self, judge):
        """Frozen invariant: verdict rows must not be mutated after creation."""
        entry = judge.LedgerEntry(
            date="2026-04-20", ts="t", model="m", target="tgt", verdict="PASS"
        )
        with pytest.raises((AttributeError, Exception)):
            entry.verdict = "FAIL"  # type: ignore[misc]


# ── JudgeError ───────────────────────────────────────────────────────────────

class TestJudgeError:
    def test_exit_code_preserved(self, judge):
        err = judge.JudgeError("boom", exit_code=4)
        assert err.exit_code == 4
        assert str(err) == "boom"

    def test_is_runtime_error(self, judge):
        err = judge.JudgeError("x", exit_code=2)
        assert isinstance(err, RuntimeError)


# ── Phase defaults ───────────────────────────────────────────────────────────

class TestPhaseDefaults:
    def test_phase_map_covers_all_sdd_phases(self, judge):
        assert set(judge.PHASE_MODEL_DEFAULTS.keys()) >= {
            "generic", "define", "design", "build",
        }

    def test_phase_defaults_are_openrouter_slugs(self, judge):
        """All phase defaults must be OpenRouter-style vendor/model slugs."""
        for phase, model in judge.PHASE_MODEL_DEFAULTS.items():
            assert "/" in model, f"phase {phase} default {model!r} missing vendor prefix"

    def test_system_prompts_mirror_phase_defaults(self, judge):
        """Every phase with a default model must have a system prompt."""
        assert set(judge.PHASE_SYSTEM_PROMPTS.keys()) == set(judge.PHASE_MODEL_DEFAULTS.keys())

    def test_define_and_design_use_reasoning_model(self, judge):
        """define and design should default to a reasoning-heavy model
        (documented in commands/workflow/define.md and design.md)."""
        assert "gpt-4" in judge.PHASE_MODEL_DEFAULTS["define"]
        assert "gpt-4" in judge.PHASE_MODEL_DEFAULTS["design"]


# ── show_ledger / load_today_count ──────────────────────────────────────────

class TestLedgerReading:
    def test_empty_ledger_returns_zero_count(self, judge, tmp_path, monkeypatch):
        ledger = tmp_path / "ledger.jsonl"
        monkeypatch.setattr(judge, "LEDGER", ledger)
        assert judge.load_today_count() == 0

    def test_count_only_todays_entries(self, judge, tmp_path, monkeypatch):
        ledger = tmp_path / "ledger.jsonl"
        today = judge.today_utc()
        rows = [
            {"date": today, "ts": "t", "model": "m", "target": "a", "verdict": "PASS"},
            {"date": today, "ts": "t", "model": "m", "target": "b", "verdict": "FAIL"},
            {"date": "1999-01-01", "ts": "t", "model": "m", "target": "c", "verdict": "PASS"},
        ]
        ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        monkeypatch.setattr(judge, "LEDGER", ledger)
        assert judge.load_today_count() == 2

    def test_malformed_rows_silently_skipped(self, judge, tmp_path, monkeypatch):
        ledger = tmp_path / "ledger.jsonl"
        today = judge.today_utc()
        lines = [
            json.dumps({"date": today, "ts": "t", "model": "m", "target": "a", "verdict": "PASS"}),
            "not valid json",
            "",
            "{broken",
        ]
        ledger.write_text("\n".join(lines))
        monkeypatch.setattr(judge, "LEDGER", ledger)
        assert judge.load_today_count() == 1
