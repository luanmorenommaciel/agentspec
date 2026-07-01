"""CLI: exit codes and spec resolution, with the evaluator stubbed (no network)."""

from __future__ import annotations

import spec_judge.openrouter as openrouter_module
from _helpers import concern, result
from spec_judge.cli import main

_SPEC_YAML = (
    "id: code-reviewer\n"
    "description: Reviews diffs.\n"
    "output_contract:\n"
    "  format: structured-report\n"
    "  required_fields: [summary]\n"
    "  side_effects: {files_written: false, git_operations: [none], external_apis: []}\n"
)


def _install_stub(monkeypatch, script) -> None:
    class Stub:
        name = "stub"

        def __init__(self, *args, **kwargs) -> None:
            pass

        def evaluate(self, request):
            return script(request)

    monkeypatch.setattr(openrouter_module, "OpenRouterEvaluator", Stub)


def _artifact(tmp_path, text: str):
    path = tmp_path / "agent.md"
    path.write_text(text)
    return path


def _spec(tmp_path):
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

    def script(request):
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

    def script(request):
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
