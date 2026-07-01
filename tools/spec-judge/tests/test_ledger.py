"""Ledger: workspace-rooted path, today-only counting, malformed-row tolerance,
shared-budget compatibility with V0 rows, and preflight."""

from __future__ import annotations

import json

import pytest

from spec_judge import ledger as L


def test_empty_ledger_is_zero(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    assert L.today_count() == 0


def test_append_then_count(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    L.append("model-a", "fault-seeker", "WARN")
    L.append("model-a", "arbiter", "PASS")
    assert L.today_count() == 2


def test_counts_only_today(tmp_path, monkeypatch) -> None:
    path = tmp_path / "l.jsonl"
    monkeypatch.setenv("JUDGE_LEDGER", str(path))
    rows = [
        {"date": L.today_utc(), "ts": "t", "model": "m", "role": "r", "verdict": "PASS"},
        {"date": "1999-01-01", "ts": "t", "model": "m", "role": "r", "verdict": "FAIL"},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    assert L.today_count() == 1


def test_malformed_rows_skipped(tmp_path, monkeypatch) -> None:
    path = tmp_path / "l.jsonl"
    monkeypatch.setenv("JUDGE_LEDGER", str(path))
    good = json.dumps(
        {"date": L.today_utc(), "ts": "t", "model": "m", "role": "r", "verdict": "PASS"}
    )
    path.write_text("\n".join([good, "not json", "", "{broken"]))
    assert L.today_count() == 1


def test_shared_budget_counts_v0_target_rows(tmp_path, monkeypatch) -> None:
    # V0 rows carry "target" not "role"; the Judger must still count them — one budget.
    path = tmp_path / "l.jsonl"
    monkeypatch.setenv("JUDGE_LEDGER", str(path))
    v0_row = {
        "date": L.today_utc(),
        "ts": "t",
        "model": "m",
        "target": "file.md",
        "verdict": "PASS",
    }
    path.write_text(json.dumps(v0_row) + "\n")
    assert L.today_count() == 1


def test_preflight_allows_up_to_ceiling_then_blocks(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    monkeypatch.setenv("JUDGE_BUDGET", "3")
    L.append("m", "fault-seeker", "PASS")  # 1 used
    L.preflight(2)  # 1 + 2 == 3, at the ceiling: allowed
    with pytest.raises(L.BudgetError):
        L.preflight(3)  # 1 + 3 == 4 > 3


def test_ledger_path_resolves_to_workspace_dot_claude(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "project"
    (workspace / ".claude").mkdir(parents=True)
    sub = workspace / "a" / "b"
    sub.mkdir(parents=True)
    monkeypatch.delenv("JUDGE_LEDGER", raising=False)
    monkeypatch.chdir(sub)
    resolved = L.ledger_path()
    assert resolved == workspace / ".claude" / "storage" / "judge-ledger.jsonl"
