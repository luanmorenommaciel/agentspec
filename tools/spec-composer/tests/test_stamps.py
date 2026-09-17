"""Tests for stamp digests, run identity, and append-only log tolerance."""

from __future__ import annotations

import json
import re
from pathlib import Path

from spec_composer.contract import Stage, bound_contract_name
from spec_composer.models import StageRecord
from spec_composer.runstate import RunLog, digest, run_dir


def test_hash_changes_when_contract_version_changes() -> None:
    content = b"hello world"
    first = digest(content, contract_version=1, contract_name="creation-spec")
    second = digest(content, contract_version=2, contract_name="creation-spec")
    assert first != second
    for rendered in (first, second):
        prefix, _, hex_digest = rendered.partition(":")
        assert prefix == "sha256"
        assert re.fullmatch(r"[0-9a-f]{64}", hex_digest) is not None


def test_hash_changes_when_bound_contract_name_changes() -> None:
    content = b"hello world"
    first = digest(content, contract_version=1, contract_name="creation-spec")
    second = digest(content, contract_version=1, contract_name="agent-spec")
    assert first != second


def test_bound_contract_name_is_kind_aware() -> None:
    """A generate stage's digest binds to its own output, never to the input
    contract its preceding gate already stamped, or the two would collide."""
    create_stage = Stage(id="create-spec", kind="create", output_contract="creation-spec")
    gate = Stage(id="gate-a", kind="lint", input_contract="creation-spec")
    generate_stage = Stage(
        id="generate-agent",
        kind="generate",
        input_contract="creation-spec",
        output_contract="agent-spec",
    )
    judge_stage = Stage(id="judge-agent", kind="judge", judge_tier="standard")
    emit_stage = Stage(id="emit-agent", kind="emit")

    assert bound_contract_name(create_stage) == "creation-spec"
    assert bound_contract_name(generate_stage) == "agent-spec"
    assert bound_contract_name(gate) == "creation-spec"
    assert bound_contract_name(judge_stage) == "spec-conformance"
    assert bound_contract_name(emit_stage) == "emit"
    assert bound_contract_name(generate_stage) != bound_contract_name(gate)


def test_torn_trailing_line_is_ignored(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    valid_stamp = json.dumps(
        {
            "ts": "2026-01-01T00:00:00+00:00",
            "kind": "stamp",
            "stage": "gate-a",
            "stage_kind": "lint",
            "attempt": 1,
            "attempts_spent": 0,
        }
    )
    valid_spend = json.dumps(
        {
            "ts": "2026-01-01T00:00:01+00:00",
            "kind": "spend",
            "stage": "gate-a",
            "stage_kind": "lint",
            "attempt": 1,
            "attempts_spent": 1,
        }
    )
    foreign_row = json.dumps({"unexpected": "shape"})
    torn_row = '{"ts": "2026-01-01T00:00:02+00:00", "kind": "stamp", "stage": "gate-'
    path.write_text(f"{valid_stamp}\n{valid_spend}\n{foreign_row}\n{torn_row}\n", encoding="utf-8")

    log = RunLog(path)
    records = log.records()

    assert [record.kind for record in records] == ["stamp", "spend"]
    assert StageRecord.from_json(foreign_row) is None
    assert StageRecord.from_json(torn_row) is None

    folded = log.fold()
    assert folded.attempts_spent == 1
    assert folded.attempt == 2


def test_same_stem_different_targets_do_not_share_a_run(tmp_path: Path) -> None:
    target_a = tmp_path / "alpha" / "code-reviewer.md"
    target_b = tmp_path / "beta" / "code-reviewer.md"

    dir_a = run_dir("agent-creation", target_a)
    dir_b = run_dir("agent-creation", target_b)

    assert dir_a != dir_b
    assert run_dir("agent-creation", target_a) == dir_a
    fingerprint = dir_a.name.rsplit("-", 1)[-1]
    assert re.fullmatch(r"[0-9a-f]{12}", fingerprint) is not None


def test_fold_on_absent_log_is_the_empty_state(tmp_path: Path) -> None:
    log = RunLog(tmp_path / "missing" / "run.jsonl")
    folded = log.fold()
    assert folded.epoch == 1
    assert folded.attempts_spent == 0
    assert folded.attempt == 1
    assert folded.approvals == frozenset()
    assert folded.stamps == ()
    assert folded.epoch_stamps == ()
    assert folded.last_spend is None
