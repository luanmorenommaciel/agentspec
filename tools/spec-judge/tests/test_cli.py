"""CLI: exit codes and spec resolution, with the evaluator stubbed (no network)."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

import spec_judge.cli as cli_module
import spec_judge.openrouter as openrouter_module
from _helpers import concern, result
from spec_judge.cli import main
from spec_judge.evaluator import EvalRequest, EvalResult

_SPEC_YAML = (
    "id: code-reviewer\n"
    "description: Reviews diffs.\n"
    "output_contract:\n"
    "  format: structured-report\n"
    "  required_fields: [summary]\n"
    "  side_effects: {files_written: false, git_operations: [none], external_apis: []}\n"
)


def _install_stub(monkeypatch, script: Callable[[EvalRequest], EvalResult]) -> None:
    # Patches the definition site (`openrouter_module.OpenRouterEvaluator`), not a
    # reference held by another module — correct only because `cli.py`/`panel.py`
    # both import `OpenRouterEvaluator` lazily (inside a function body) rather than
    # binding their own top-level name to it at import time.
    class Stub:
        name = "stub"

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def evaluate(self, request: EvalRequest) -> EvalResult:
            return script(request)

    monkeypatch.setattr(openrouter_module, "OpenRouterEvaluator", Stub)


def _artifact(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "agent.md"
    path.write_text(text)
    return path


def _spec(tmp_path: Path) -> Path:
    path = tmp_path / "spec.yaml"
    path.write_text(_SPEC_YAML)
    return path


def test_exit_0_on_clean(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    _install_stub(monkeypatch, lambda r: result(r.role, cross_model=r.cross_model))
    rc = main(
        [
            str(_artifact(tmp_path, "A body honoring the contract.")),
            "--spec",
            str(_spec(tmp_path)),
            "--tier",
            "smoke",
        ]
    )
    assert rc == 0


def test_warn_is_exit_0(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    _install_stub(
        monkeypatch,
        lambda r: result(r.role, cross_model=r.cross_model, concerns=[concern("B1", "high")]),
    )
    rc = main(
        [
            str(_artifact(tmp_path, "vague body")),
            "--spec",
            str(_spec(tmp_path)),
            "--tier",
            "standard",
        ]
    )
    assert rc == 0  # WARN never blocks
    assert "WARN" in capsys.readouterr().out


def test_high_assurance_fail_is_exit_1(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    monkeypatch.setenv("JUDGE_BUDGET", "100")

    def script(request: EvalRequest) -> EvalResult:
        raised = [concern("B2", "high")] if request.role in ("fault-seeker", "arbiter") else []
        return result(
            request.role, cross_model=request.cross_model, confidence=0.9, concerns=raised
        )

    _install_stub(monkeypatch, script)
    rc = main(
        [
            str(_artifact(tmp_path, "omits the required field")),
            "--spec",
            str(_spec(tmp_path)),
            "--tier",
            "high-assurance",
        ]
    )
    assert rc == 1


def test_missing_artifact_is_exit_2(tmp_path) -> None:
    assert main([str(tmp_path / "nope.md"), "--tier", "smoke"]) == 2


def test_no_spec_and_no_frontmatter_is_exit_2(tmp_path) -> None:
    assert main([str(_artifact(tmp_path, "body without frontmatter")), "--tier", "smoke"]) == 2


def test_frontmatter_used_as_spec(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    _install_stub(monkeypatch, lambda r: result(r.role, cross_model=r.cross_model))
    art = _artifact(
        tmp_path,
        "---\nid: x\noutput_contract:\n  required_fields: [summary]\n---\nThe body honoring it.\n",
    )
    assert main([str(art), "--tier", "smoke"]) == 0


def test_budget_exhausted_is_exit_3(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    monkeypatch.setenv("JUDGE_BUDGET", "0")
    _install_stub(monkeypatch, lambda r: result(r.role))
    rc = main([str(_artifact(tmp_path, "body")), "--spec", str(_spec(tmp_path)), "--tier", "smoke"])
    assert rc == 3


def test_network_failure_is_exit_4(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    monkeypatch.setenv("JUDGE_BUDGET", "100")

    def script(request: EvalRequest) -> EvalResult:
        raise openrouter_module.NetworkError("boom")

    _install_stub(monkeypatch, script)
    rc = main([str(_artifact(tmp_path, "body")), "--spec", str(_spec(tmp_path)), "--tier", "smoke"])
    assert rc == 4


def test_selfcheck_is_exit_0() -> None:
    assert main(["--selfcheck"]) == 0


def test_ledger_command_is_exit_0(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    assert main(["--ledger"]) == 0
    assert "Today:" in capsys.readouterr().out


def test_directory_as_artifact_is_exit_2(tmp_path) -> None:
    assert main([str(tmp_path), "--tier", "smoke"]) == 2


def test_directory_as_spec_is_exit_2(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    art = _artifact(tmp_path, "body without frontmatter")
    assert main([str(art), "--spec", str(tmp_path), "--tier", "smoke"]) == 2


def test_judging_path_generic_exception_is_exit_2(tmp_path, monkeypatch) -> None:
    # Pins the catch-all: an unexpected exception anywhere in the judging path (not
    # just the typed BudgetError/NetworkError/ConfigError) must degrade to exit 2.
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))

    def _boom(args: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "_build_panel", _boom)
    rc = main([str(_artifact(tmp_path, "body")), "--spec", str(_spec(tmp_path)), "--tier", "smoke"])
    assert rc == 2


def test_missing_sibling_package_degrades_to_exit_2(tmp_path) -> None:
    pkg_root = Path(__file__).resolve().parents[1]  # tools/spec-judge (spec_linter NOT here)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pkg_root)
    env.pop("OPENROUTER_API_KEY", None)

    probe = subprocess.run(
        [sys.executable, "-c", "import spec_linter"],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    if probe.returncode == 0:
        pytest.skip("missing-sibling scenario not reproducible: spec_linter installed")

    artifact = tmp_path / "agent.md"
    artifact.write_text(
        "---\nid: x\noutput_contract:\n  required_fields: [summary]\n---\nA body.\n"
    )
    completed = subprocess.run(
        [sys.executable, "-m", "spec_judge.cli", str(artifact), "--tier", "smoke"],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "ERROR" in completed.stderr


def test_urlopen_timeout_maps_to_exit_4(tmp_path, monkeypatch) -> None:
    # End-to-end with the REAL OpenRouterEvaluator (not stubbed): a genuine mid-request
    # TimeoutError must surface as exit 4, never an uncaught crash.
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    def fake_urlopen(*args: object, **kwargs: object) -> None:
        raise TimeoutError("stalled")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    rc = main([str(_artifact(tmp_path, "body")), "--spec", str(_spec(tmp_path)), "--tier", "smoke"])
    assert rc == 4


def test_spec_flag_still_strips_the_artifacts_own_frontmatter(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    seen_bodies: list[str] = []

    def script(request: EvalRequest) -> EvalResult:
        seen_bodies.append(request.artifact_text)
        return result(request.role, cross_model=request.cross_model)

    _install_stub(monkeypatch, script)
    art = _artifact(
        tmp_path,
        "---\nid: from-artifact\noutput_contract:\n  required_fields: [x]\n---\nThe real body.\n",
    )
    rc = main([str(art), "--spec", str(_spec(tmp_path)), "--tier", "smoke"])
    assert rc == 0
    assert seen_bodies  # sanity: the evaluator actually ran
    assert all("output_contract:" not in body for body in seen_bodies)
    assert all("The real body." in body for body in seen_bodies)


def test_high_assurance_model_collision_with_alt_default_is_exit_2(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    monkeypatch.setenv("JUDGE_BUDGET", "100")
    _install_stub(monkeypatch, lambda r: result(r.role, cross_model=r.cross_model))
    rc = main(
        [
            str(_artifact(tmp_path, "body")),
            "--spec",
            str(_spec(tmp_path)),
            "--tier",
            "high-assurance",
            "--model",
            "anthropic/claude-sonnet-5",
        ]
    )
    assert rc == 2


def test_oversized_body_is_exit_2(tmp_path) -> None:
    huge = "x" * 200_001
    rc = main([str(_artifact(tmp_path, huge)), "--spec", str(_spec(tmp_path)), "--tier", "smoke"])
    assert rc == 2


def test_json_output_emits_level_names(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    _install_stub(
        monkeypatch,
        lambda r: result(r.role, cross_model=r.cross_model, concerns=[concern("B1", "high")]),
    )
    rc = main(
        [
            str(_artifact(tmp_path, "vague body")),
            "--spec",
            str(_spec(tmp_path)),
            "--tier",
            "standard",
            "--json",
        ]
    )
    assert rc == 0
    assert '"level": "WARN"' in capsys.readouterr().out


def test_spec_flag_with_whitespace_only_body_is_exit_2_never_1(tmp_path) -> None:
    rc = main(
        [str(_artifact(tmp_path, "   \n\t  ")), "--spec", str(_spec(tmp_path)), "--tier", "smoke"]
    )
    assert rc == 2
