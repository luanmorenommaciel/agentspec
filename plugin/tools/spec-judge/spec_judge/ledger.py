"""Shared per-day evaluation budget ledger.

An append-only JSONL record of model calls that caps spend per UTC day. It is shared
with the V0 reviewer so the whole judge family draws on one budget — counting is by
``date`` only, so entries written in either schema count against the same ceiling.

The ledger path resolves from the **workspace** (the nearest ancestor with a
``.claude/`` directory), never from this module's location: at plugin runtime the
package lives under the install dir, and resolving from ``__file__`` would hide the
ledger there and split the budget. ``JUDGE_LEDGER`` overrides the path outright.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEFAULT_BUDGET = 10
_LEDGER_RELATIVE = Path(".claude") / "storage" / "judge-ledger.jsonl"


class BudgetError(RuntimeError):
    """Raised when a panel would exceed the per-day budget."""


def ledger_path() -> Path:
    override = os.environ.get("JUDGE_LEDGER")
    if override:
        return Path(override).expanduser()
    cwd = Path.cwd().resolve()
    for base in (cwd, *cwd.parents):
        if (base / ".claude").is_dir():
            return base / _LEDGER_RELATIVE
    return cwd / _LEDGER_RELATIVE


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    date: str
    ts: str
    model: str
    verdict: str
    role: str = ""
    target: str = ""  # read for compatibility with V0 rows; unused by the Judger's writes
    cost_usd: float | None = None

    @classmethod
    def from_json(cls, raw: str) -> LedgerEntry | None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        return cls(
            date=str(data.get("date", "")),
            ts=str(data.get("ts", "")),
            model=str(data.get("model", "")),
            verdict=str(data.get("verdict", "")),
            role=str(data.get("role", "")),
            target=str(data.get("target", "")),
            cost_usd=data.get("cost_usd"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v not in (None, "") or k == "cost_usd"}


def today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def _read_entries() -> list[LedgerEntry]:
    path = ledger_path()
    if not path.exists():
        return []
    entries: list[LedgerEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        entry = LedgerEntry.from_json(stripped)
        if entry is not None:
            entries.append(entry)
    return entries


def today_count() -> int:
    today = today_utc()
    return sum(1 for entry in _read_entries() if entry.date == today)


def budget() -> int:
    try:
        return int(os.environ.get("JUDGE_BUDGET", DEFAULT_BUDGET))
    except ValueError:
        return DEFAULT_BUDGET


def append(model: str, role: str, verdict: str, cost_usd: float | None = None) -> None:
    path = ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = LedgerEntry(
        date=today_utc(),
        ts=dt.datetime.now(dt.timezone.utc).isoformat(),
        model=model,
        verdict=verdict,
        role=role,
        cost_usd=cost_usd,
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.to_dict()) + "\n")


def preflight(seat_count: int) -> None:
    """Refuse to start a panel that cannot finish within today's remaining budget."""
    used = today_count()
    cap = budget()
    if used + seat_count > cap:
        raise BudgetError(
            f"panel needs {seat_count} calls; {used}/{cap} already used today — would exceed budget"
        )
