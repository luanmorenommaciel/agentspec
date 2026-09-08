"""CLI surface: the five-code exit table, the check mode, selfcheck and approvals."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml
from _helpers import (
    AGENT_TEXT,
    EXAMPLES,
    REJECTED_AGENT_TEXT,
    SHIPPED_PIPELINE,
    SPEC_TEXT,
    TOOL_ROOT,
)

from spec_composer.cli import main

_REASONS = (
    "awaiting-artifact",
    "stale-artifact",
    "no-progress",
    "approval-outstanding",
    "judge-unavailable",
    "budget-exhausted",
    "no-feedback-target",
    "high-assurance-judge-fail",
    "judge-unparseable",
    "promotion-failed",
    "archive-failed",
    "target-modified",
)

# A failure before the run starts has no disposition of its own; these are the
# reasons the CLI renders for one.
_PRE_RUN_REASONS = (
    "contract-unloadable",
    "linter-absent",
    "contract-invalid",
    "out-required",
    "spec-not-found",
    "run-failed",
)


def _write_spec(tmp_path: Path) -> Path:
    path = tmp_path / "code-reviewer.spec.md"
    path.write_text(SPEC_TEXT, encoding="utf-8")
    return path


def _pipeline(tmp_path: Path, *, drop_judge: bool = True, **overrides: object) -> Path:
    document = yaml.safe_load(SHIPPED_PIPELINE.read_text(encoding="utf-8"))
    if drop_judge:
        document["stages"] = [s for s in document["stages"] if s["kind"] != "judge"]
    document.update(overrides)
    path = tmp_path / f"pipeline-{len(list(tmp_path.glob('pipeline-*.yaml')))}.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def _run_json(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, dict[str, object]]:
    code = main([*argv, "--json"])
    return code, json.loads(capsys.readouterr().out)


def _stage_artifact(payload: dict[str, object], body: str) -> Path:
    """Write the artifact the conductor reported it is waiting for."""
    staged = Path(str(payload["expected_path"]))
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(body, encoding="utf-8")
    return staged


def test_check_shipped_pipeline_passes(capsys: pytest.CaptureFixture[str]) -> None:
    """The conductor's own configuration is a valid artifact of its own schema."""
    assert main(["--check", str(SHIPPED_PIPELINE)]) == 0
    assert "VERDICT: PASS" in capsys.readouterr().out


def test_check_ordering_violation_fails_with_rule_name(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The cheap-before-expensive invariant is falsifiable: the violating contract
    is expressible and its check names the rule that rejected it."""
    code = main(["--check", str(EXAMPLES / "invalid_judge_before_gate.yaml")])
    out = capsys.readouterr().out
    assert code == 1
    assert "VERDICT: FAIL" in out
    assert "P2.judge_after_gates" in out


def test_check_is_a_verdict_surface_but_a_run_is_not(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The same invalid contract is a FAIL verdict under --check (exit 1) and an
    operational error during a run (exit 2): the run could not start at all."""
    invalid = EXAMPLES / "invalid_judge_before_gate.yaml"
    assert main(["--check", str(invalid)]) == 1
    capsys.readouterr()
    code = main([str(_write_spec(tmp_path)), "--pipeline", str(invalid), "--out", "out.md"])
    assert code == 2


def test_missing_staged_artifact_exits_waiting(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = _write_spec(tmp_path)
    code, payload = _run_json(
        [str(spec), "--pipeline", str(_pipeline(tmp_path)), "--out", "agents/code-reviewer.md"],
        capsys,
    )
    assert code == 4
    assert payload["disposition"] == "waiting"
    assert payload["reason"] == "awaiting-artifact"
    expected = Path(str(payload["expected_path"]))
    assert expected.name == "code-reviewer.md"
    assert "staging" in expected.parts and "attempt-1" in expected.parts


def test_waiting_prints_path_and_reason(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A host that cannot read JSON still learns what to produce and why."""
    spec = _write_spec(tmp_path)
    code = main([str(spec), "--pipeline", str(_pipeline(tmp_path)), "--out", "a/code-reviewer.md"])
    out = capsys.readouterr().out
    assert code == 4
    assert "DISPOSITION: WAITING (awaiting-artifact)" in out
    assert "expected at:" in out


def test_waiting_then_identical_rerun_completes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The staged handoff: report the path, let the host write it, re-run the
    identical command."""
    argv = [
        str(_write_spec(tmp_path)),
        "--pipeline",
        str(_pipeline(tmp_path)),
        "--out",
        "agents/code-reviewer.md",
    ]
    first, payload = _run_json(argv, capsys)
    assert first == 4
    _stage_artifact(payload, AGENT_TEXT)
    second, final = _run_json(argv, capsys)
    assert second == 0
    assert final["disposition"] == "emitted"
    assert Path("agents/code-reviewer.md").read_text(encoding="utf-8") == AGENT_TEXT


@pytest.mark.parametrize("disposition,expected", [("emitted", 0), ("blocked", 1), ("paused", 3)])
def test_exit_code_table(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], disposition: str, expected: int
) -> None:
    """Every non-zero code is a distinct non-PASS disposition."""
    if disposition == "paused":
        pipeline = EXAMPLES / "emit_requires_approval.yaml"
        body = AGENT_TEXT
    else:
        pipeline = _pipeline(tmp_path, max_attempts=1 if disposition == "blocked" else 3)
        body = REJECTED_AGENT_TEXT if disposition == "blocked" else AGENT_TEXT
    argv = [str(_write_spec(tmp_path)), "--pipeline", str(pipeline), "--out", "a/code-reviewer.md"]
    first, payload = _run_json(argv, capsys)
    assert first == 4
    _stage_artifact(payload, body)
    code, final = _run_json(argv, capsys)
    assert code == expected
    assert final["disposition"] == disposition


@pytest.mark.parametrize(
    ("cause", "evidence"),
    [
        ("invalid-contract", "is invalid"),
        ("unresolvable-reference", "no contract is bound to 'kb-spec'"),
        ("missing-spec", "spec not found"),
        ("linter-absent", "cannot import spec_linter"),
    ],
)
def test_exit_code_table_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    cause: str,
    evidence: str,
) -> None:
    """Exit 2 is the configuration-defect bucket: re-running cannot clear it. Each
    cause has to say which defect it was, or the bucket is unactionable."""
    spec = _write_spec(tmp_path)
    pipeline = _pipeline(tmp_path)
    argv = [str(spec), "--pipeline", str(pipeline), "--out", "a/code-reviewer.md"]
    if cause == "invalid-contract":
        argv[2] = str(EXAMPLES / "invalid_ungated_emit.yaml")
    elif cause == "unresolvable-reference":
        document = yaml.safe_load(pipeline.read_text(encoding="utf-8"))
        for stage in document["stages"]:
            if stage.get("output_contract") == "creation-spec":
                stage["output_contract"] = "kb-spec"
            if stage.get("input_contract") == "creation-spec":
                stage["input_contract"] = "kb-spec"
        pipeline.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    elif cause == "missing-spec":
        argv[0] = str(tmp_path / "absent.spec.md")
    else:
        monkeypatch.setitem(sys.modules, "spec_linter", None)
    assert main(argv) == 2
    captured = capsys.readouterr().err
    assert "ERROR" in captured
    assert evidence in captured


def test_blocked_reason_distinguishes_budget_from_high_assurance(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both causes exit 1; only the reason tells an operator which one happened."""
    argv = [
        str(_write_spec(tmp_path)),
        "--pipeline",
        str(_pipeline(tmp_path, max_attempts=1)),
        "--out",
        "a/code-reviewer.md",
    ]
    _, payload = _run_json(argv, capsys)
    _stage_artifact(payload, REJECTED_AGENT_TEXT)
    code, exhausted = _run_json(argv, capsys)
    assert code == 1
    assert exhausted["reason"] == "budget-exhausted"

    from spec_linter import Finding, Level, Verdict

    monkeypatch.setattr(
        "spec_composer.engine.judge_artifact",
        lambda *args, **kwargs: Verdict.from_findings(
            [Finding(level=Level.FAIL, rule="B2.capability", message="not delivered")]
        ),
    )
    document = yaml.safe_load(SHIPPED_PIPELINE.read_text(encoding="utf-8"))
    for stage in document["stages"]:
        if stage["kind"] == "judge":
            stage["judge_tier"] = "high-assurance"
    strict = tmp_path / "strict.yaml"
    strict.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    argv = [str(_write_spec(tmp_path)), "--pipeline", str(strict), "--out", "b/code-reviewer.md"]
    _, payload = _run_json(argv, capsys)
    _stage_artifact(payload, AGENT_TEXT)
    code, blocked = _run_json(argv, capsys)
    assert code == 1
    assert blocked["reason"] == "high-assurance-judge-fail"
    assert not Path("b/code-reviewer.md").exists()


def test_approve_flag_clears_pause(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """An approval class the contract requires can only be satisfied, never added
    or removed, by operator input — and the grant persists in the evidence log."""
    argv = [
        str(_write_spec(tmp_path)),
        "--pipeline",
        str(EXAMPLES / "emit_requires_approval.yaml"),
        "--out",
        "a/code-reviewer.md",
    ]
    _, payload = _run_json(argv, capsys)
    _stage_artifact(payload, AGENT_TEXT)
    paused, outstanding = _run_json(argv, capsys)
    assert paused == 3
    assert outstanding["reason"] == "approval-outstanding:publish"
    assert not Path("a/code-reviewer.md").exists()

    granted, final = _run_json([*argv, "--approve", "publish"], capsys)
    assert granted == 0
    assert final["disposition"] == "emitted"
    assert Path("a/code-reviewer.md").exists()

    resumed, again = _run_json(argv, capsys)
    assert resumed == 0
    assert again["disposition"] == "emitted"


@pytest.mark.parametrize(
    "cause", ["missing-credential", "budget-exhausted", "provider-unreachable", "sibling-absent"]
)
def test_judge_unavailable_exits_paused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, cause: str
) -> None:
    """Unavailability never equals PASS: a bound-but-unrunnable judge pauses."""
    if cause == "budget-exhausted":
        monkeypatch.setenv("JUDGE_BUDGET", "0")
    elif cause == "provider-unreachable":
        monkeypatch.setenv("OPENROUTER_API_KEY", "present-but-unreachable")
        from spec_judge.openrouter import NetworkError, OpenRouterEvaluator

        def _unreachable(self: object, request: object) -> None:
            raise NetworkError("provider unreachable")

        monkeypatch.setattr(OpenRouterEvaluator, "evaluate", _unreachable)
    elif cause == "sibling-absent":
        monkeypatch.setitem(sys.modules, "spec_judge.engine", None)

    argv = [
        str(_write_spec(tmp_path)),
        "--pipeline",
        str(SHIPPED_PIPELINE),
        "--out",
        "a/code-reviewer.md",
    ]
    _, payload = _run_json(argv, capsys)
    _stage_artifact(payload, AGENT_TEXT)
    code, final = _run_json(argv, capsys)
    assert code == 3
    assert final["disposition"] == "paused"
    assert final["reason"] == "judge-unavailable"
    assert not Path("a/code-reviewer.md").exists()
    assert not any(entry["stage"] == "judge-agent" for entry in final["trail"])


def test_selfcheck_reports_judge_availability(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--selfcheck"]) == 0
    assert "spec_linter" in capsys.readouterr().out


def test_selfcheck_exits_two_without_linter(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hard sibling degrades loudly rather than silently skipping a gate."""
    monkeypatch.setitem(sys.modules, "spec_linter", None)
    assert main(["--selfcheck"]) == 2
    assert "cannot import spec_linter" in capsys.readouterr().err


def test_check_without_a_path_is_rejected() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--check"])
    assert excinfo.value.code == 2


def test_usage_documents_every_exit_code() -> None:
    """The exit contract is only usable if the operator document carries it."""
    usage = (TOOL_ROOT / "USAGE.md").read_text(encoding="utf-8")
    for disposition in ("emitted", "blocked", "error", "paused", "waiting"):
        assert disposition in usage
    for reason in _REASONS:
        assert reason in usage, reason
    assert ">= 2" in usage or "≥ 2" in usage


@pytest.mark.parametrize(
    ("cause", "reason", "code"),
    [
        ("missing-contract", "contract-unloadable", 2),
        ("invalid-contract", "contract-invalid", 2),
        ("missing-spec", "spec-not-found", 2),
        ("no-out", "out-required", 2),
    ],
)
def test_pre_run_failures_render_as_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], cause: str, reason: str, code: int
) -> None:
    """A host that asked for JSON gets JSON on every path. A failure before the
    first stage has no disposition of its own, so it is rendered as one rather
    than as a bare stderr line the caller then has to parse differently."""
    argv = [
        str(_write_spec(tmp_path)),
        "--pipeline",
        str(_pipeline(tmp_path)),
        "--out",
        "a/code-reviewer.md",
    ]
    if cause == "missing-contract":
        argv[2] = str(tmp_path / "absent.yaml")
    elif cause == "invalid-contract":
        argv[2] = str(EXAMPLES / "invalid_ungated_emit.yaml")
    elif cause == "missing-spec":
        argv[0] = str(tmp_path / "absent.spec.md")
    else:
        argv = argv[:3]

    assert main([*argv, "--json"]) == code
    payload = json.loads(capsys.readouterr().out)
    assert payload["disposition"] == "error"
    assert payload["reason"] == reason
    assert payload["detail"]


def test_check_on_a_non_mapping_document_is_a_fail_not_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--check` is a verdict surface: a document that loads but is not a pipeline
    contract gets the FAIL its own contract defines. Only a path that cannot be
    read at all is an unloadable file."""
    document = tmp_path / "not-a-contract.yaml"
    document.write_text("- create\n- lint\n- emit\n", encoding="utf-8")

    assert main(["--check", str(document)]) == 1
    out = capsys.readouterr().out
    assert "VERDICT: FAIL" in out
    assert "pipeline-contract.unparseable" in out

    assert main(["--check", str(tmp_path / "absent.yaml")]) == 2
    assert "not found" in capsys.readouterr().err


def test_pipeline_pointing_at_a_directory_reports_what_is_wrong(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A directory is a plausible mistype of a contract path; the message says so
    instead of surfacing the operating system's read error."""
    argv = [str(_write_spec(tmp_path)), "--pipeline", str(tmp_path), "--out", "a/x.md"]
    assert main(argv) == 2
    assert "not a file" in capsys.readouterr().err


def test_usage_documents_the_operator_recovery_paths() -> None:
    """Every stop the conductor can reach has to be clearable from the document
    alone: where the run state lands with no workspace marker, how a modified
    target is re-promoted, and why an archive can refuse to be written."""
    usage = (TOOL_ROOT / "USAGE.md").read_text(encoding="utf-8")
    for reason in _PRE_RUN_REASONS:
        assert reason in usage, reason
    assert "unique" in usage
    assert "working directory" in usage
