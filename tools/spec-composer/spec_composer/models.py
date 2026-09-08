"""Frozen value objects for one composition run.

The verdict vocabulary is the Linter's — `Verdict`, `Finding` and `Level` are
imported, never re-declared. Everything here describes operational outcome: what
the conductor was asked to do, what each stage recorded, and how the run ended.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError
from spec_linter import Finding, Verdict

RowKind = Literal["stamp", "spend", "approval", "run-closed", "event"]


class Disposition(StrEnum):
    EMITTED = "emitted"
    BLOCKED = "blocked"
    ERROR = "error"
    PAUSED = "paused"
    WAITING = "waiting"


class ComposeRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    target: Path
    spec_path: Path | None = None
    approvals: frozenset[str] = frozenset()


class GenerationRequest(BaseModel):
    """What a producing stage hands the generator: which stage, where the output
    must appear for THIS attempt, what it was generated from, and the findings
    that sent the run back here."""

    model_config = ConfigDict(frozen=True)

    stage: str
    kind: Literal["create", "generate"]
    output_contract: str | None
    output_path: Path
    attempt: int
    input_path: Path | None = None
    input_text: str = ""
    feedback: tuple[Finding, ...] = ()


class GenerationOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    produced: bool
    path: Path
    detail: str = ""


class StageVerdict(BaseModel):
    model_config = ConfigDict(frozen=True)

    stage: str
    stage_kind: str
    contract: str
    attempt: int
    verdict: Verdict


class StageRecord(BaseModel):
    """One line of the append-only run log. Five row kinds: `stamp` (a stage
    cleared for this content under this rule), `spend` (a gate FAIL charged to
    the shared budget, carrying the derived routing target), `approval` (classes
    an operator granted), `run-closed` (a terminal disposition, which opens the
    next epoch — except a `blocked` row whose reason is `no-progress`, which is
    a stall, not a conclusion, and so stays in the current epoch) and `event`
    (a pause, a wait, or a recorded operational failure).
    """

    model_config = ConfigDict(frozen=True)

    ts: str
    kind: RowKind
    stage: str
    stage_kind: str
    attempt: int
    attempts_spent: int
    verdict: str | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    contract_id: str | None = None
    disposition: str | None = None
    reason: str | None = None
    route_to: str | None = None
    path: str | None = None
    detail: str | None = None
    approvals: tuple[str, ...] = ()
    findings: tuple[dict[str, Any], ...] = ()

    @classmethod
    def from_json(cls, raw: str) -> StageRecord | None:
        """Parse one log line, or return None for a torn or foreign row — the
        tolerance that makes a single append-only file crash-safe."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        try:
            return cls.model_validate(data)
        except ValidationError:
            return None


class ComposeResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    disposition: Disposition
    stage: str | None
    epoch: int
    attempt: int
    attempts_spent: int
    trail: tuple[StageVerdict, ...]
    run_dir: Path
    artifact: Path | None = None
    expected_path: Path | None = None
    reason: str | None = None
