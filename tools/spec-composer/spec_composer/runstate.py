"""Run state — one append-only evidence log per (pipeline, target).

The root resolves from the WORKSPACE (the nearest ancestor holding a `.claude/`
directory), never from this module's location: at plugin runtime the package
lives under the install directory, and resolving from `__file__` would hide the
run state there. `COMPOSER_RUN_ROOT` overrides the path outright. The run
directory is keyed by the RESOLVED TARGET PATH, not by its stem, so two pipelines
emitting different files never share evidence or a budget.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from .models import StageRecord

_RUN_ROOT_RELATIVE = Path(".claude") / "storage" / "composer"
_SLUG = re.compile(r"[^a-z0-9._-]+")


def workspace_root() -> Path:
    cwd = Path.cwd().resolve()
    for base in (cwd, *cwd.parents):
        if (base / ".claude").is_dir():
            return base
    return cwd


def run_root() -> Path:
    override = os.environ.get("COMPOSER_RUN_ROOT")
    if override:
        return Path(override).expanduser()
    return workspace_root() / _RUN_ROOT_RELATIVE


def slug(text: str) -> str:
    return _SLUG.sub("-", text.strip().lower()).strip("-") or "unnamed"


def run_dir(pipeline: str, target: Path) -> Path:
    """Target-keyed run identity: the stem is for humans, the digest is for
    correctness."""
    resolved = str(target.expanduser().resolve())
    fingerprint = hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:12]
    return run_root() / slug(pipeline) / f"{slug(target.stem)}-{fingerprint}"


def digest(content: bytes, *, contract_version: int, contract_name: str) -> str:
    """The certificate folded into a stamp: content, the pipeline contract version
    in force, and the name of the contract bound at that stage. A rule change
    invalidates a stamp exactly as a content change does."""
    hasher = hashlib.sha256()
    hasher.update(content)
    hasher.update(b"\0")
    hasher.update(str(contract_version).encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(contract_name.encode("utf-8"))
    return f"sha256:{hasher.hexdigest()}"


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


@dataclass(frozen=True, slots=True)
class FoldedState:
    """Everything the walk needs, recomputed from the log on every run."""

    epoch: int
    attempts_spent: int
    attempt: int
    approvals: frozenset[str]
    stamps: tuple[StageRecord, ...]
    epoch_stamps: tuple[StageRecord, ...]
    last_spend: StageRecord | None = None
    stale_waits: tuple[tuple[str, int], ...] = ()


class RunLog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: StageRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(record.model_dump(mode="json"), separators=(",", ":"))
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(payload + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def records(self) -> list[StageRecord]:
        """Every intact record. A torn trailing line is discarded, which is what
        makes a single append-only file crash-safe. A torn `spend` row therefore
        under-counts the budget by one — accepted, and visible in the log."""
        if not self.path.exists():
            return []
        rows = (
            StageRecord.from_json(line.strip())
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        return [row for row in rows if row is not None]

    def fold(self) -> FoldedState:
        rows = self.records()
        closes = [index for index, row in enumerate(rows) if row.kind == "run-closed"]
        start = closes[-1] + 1 if closes else 0
        current = rows[start:]
        spends = [row for row in current if row.kind == "spend"]
        granted: set[str] = set()
        stale_waits: dict[str, int] = {}
        for row in current:
            if row.kind == "approval":
                granted.update(row.approvals)
            elif row.kind == "stamp":
                # Evidence of progress at this stage: whatever it stamped, it was
                # not a repeat of content already stamped (`is_fresh` gates that
                # before a stamp can happen), so any run of stale-artifact waits
                # it was accumulating is over. A `spend` row is deliberately NOT
                # treated as progress here, even though its `route_to` names the
                # stage about to retry: reaching that gate at all already required
                # the routed-to stage to have produced fresh content and been
                # stamped for it (a `pending` stage can only ever re-run, never
                # skip past, its own `_produce` check), so the qualifying stamp
                # always precedes the spend and has already reset the counter.
                # Keying a reset on a spend row would also invite the wrong bug —
                # a spend's own `stage` is the GATE that failed, not the producer
                # `route_to` names, so resetting off it risks zeroing the wrong
                # stage's count.
                stale_waits[row.stage] = 0
            elif row.kind == "event" and row.reason == "stale-artifact":
                stale_waits[row.stage] = stale_waits.get(row.stage, 0) + 1
        return FoldedState(
            epoch=len(closes) + 1,
            attempts_spent=len(spends),
            attempt=len(spends) + 1,
            approvals=frozenset(granted),
            stamps=tuple(row for row in rows if row.kind == "stamp"),
            epoch_stamps=tuple(row for row in current if row.kind == "stamp"),
            last_spend=spends[-1] if spends else None,
            stale_waits=tuple(stale_waits.items()),
        )
