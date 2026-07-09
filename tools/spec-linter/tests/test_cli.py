"""Tests for the CLI: file/dir linting, exit codes, and JSON Schema emission."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from spec_linter import cli
from spec_linter.verdict import Level


def _write_spec(path: Path, spec: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump(spec))
    return path


def test_valid_file_passes_with_exit_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], valid_spec: dict[str, Any]
) -> None:
    spec_file = _write_spec(tmp_path / "agent.yaml", valid_spec)
    assert cli.main([str(spec_file)]) == 0
    assert "VERDICT: PASS" in capsys.readouterr().out


def test_failing_file_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], valid_spec: dict[str, Any]
) -> None:
    valid_spec["observability"] = None
    spec_file = _write_spec(tmp_path / "agent.yaml", valid_spec)
    assert cli.main([str(spec_file)]) == 1
    out = capsys.readouterr().out
    assert "VERDICT: FAIL" in out
    assert "L2.maturity_observability" in out


def test_dir_lint_reports_overall_and_exits_one_on_any_fail(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], valid_spec: dict[str, Any]
) -> None:
    _write_spec(tmp_path / "good.yaml", valid_spec)
    failing = {**valid_spec, "id": "another-agent", "publish": True, "security_review": False}
    _write_spec(tmp_path / "bad.yaml", failing)
    assert cli.main([str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "== good.yaml ==" in out
    assert "== bad.yaml ==" in out
    assert "OVERALL: FAIL" in out


def test_duplicate_id_across_dir_is_fail(tmp_path: Path, valid_spec: dict[str, Any]) -> None:
    _write_spec(tmp_path / "a.yaml", valid_spec)
    _write_spec(tmp_path / "b.yaml", valid_spec)  # same id in both files

    verdicts = cli._lint_dir(tmp_path)
    assert set(verdicts) == {"a.yaml", "b.yaml"}
    for name in ("a.yaml", "b.yaml"):
        assert verdicts[name].level == Level.FAIL
        dupes = [f for f in verdicts[name].findings if f.rule == "L4.duplicate_id"]
        assert len(dupes) == 1
        assert "a.yaml" in dupes[0].found and "b.yaml" in dupes[0].found


def test_emit_schema_writes_file_creating_parent_dirs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out_path = tmp_path / "nested" / "agent_spec.schema.json"
    assert cli.main(["--emit-schema", str(out_path)]) == 0
    schema = json.loads(out_path.read_text())
    assert "output_contract" in schema["properties"]
    assert f"Wrote JSON Schema to {out_path}" in capsys.readouterr().out


def test_missing_file_is_error_exit_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "does_not_exist.yaml"
    assert cli.main([str(missing)]) == 2
    assert "ERROR:" in capsys.readouterr().err


def test_malformed_yaml_is_error_exit_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "broken.yaml"
    bad.write_text("id: [unterminated\n")
    assert cli.main([str(bad)]) == 2
    assert "ERROR:" in capsys.readouterr().err


def test_non_mapping_yaml_is_error_exit_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scalar = tmp_path / "scalar.yaml"
    scalar.write_text("just a string\n")
    assert cli.main([str(scalar)]) == 2
    assert "ERROR:" in capsys.readouterr().err


def test_error_exit_two_is_distinct_from_fail_exit_one(
    tmp_path: Path, valid_spec: dict[str, Any]
) -> None:
    valid_spec["observability"] = None  # loadable mapping, contract FAIL -> exit 1
    fail_file = _write_spec(tmp_path / "fail.yaml", valid_spec)
    assert cli.main([str(fail_file)]) == 1
    assert cli.main([str(tmp_path / "nope.yaml")]) == 2  # operational ERROR -> exit 2


def _write_phase_doc(path: Path, headings: list[str]) -> Path:
    path.write_text("\n\n".join(f"## {h}" for h in headings) + "\n")
    return path


def test_phase_doc_passes_with_exit_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    contracts = tmp_path / "contracts.yaml"
    contracts.write_text(
        yaml.safe_dump({"define": {"required_sections": ["Problem Statement", "Goals"]}})
    )
    doc = _write_phase_doc(tmp_path / "DEFINE_X.md", ["Problem Statement", "Goals"])
    code = cli.main([str(doc), "--phase", "define", "--contracts-file", str(contracts)])
    assert code == 0
    assert "VERDICT: PASS" in capsys.readouterr().out


def test_phase_doc_missing_section_fails_with_exit_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    contracts = tmp_path / "contracts.yaml"
    contracts.write_text(
        yaml.safe_dump({"define": {"required_sections": ["Problem Statement", "Goals"]}})
    )
    doc = _write_phase_doc(tmp_path / "DEFINE_X.md", ["Problem Statement"])
    code = cli.main([str(doc), "--phase", "define", "--contracts-file", str(contracts)])
    assert code == 1
    out = capsys.readouterr().out
    assert "VERDICT: FAIL" in out
    assert "L2.required_section" in out


def test_phase_unknown_phase_is_error_exit_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    contracts = tmp_path / "contracts.yaml"
    contracts.write_text(yaml.safe_dump({"define": {"required_sections": ["Problem Statement"]}}))
    doc = _write_phase_doc(tmp_path / "DOC.md", ["Problem Statement"])
    code = cli.main([str(doc), "--phase", "nonexistent", "--contracts-file", str(contracts)])
    assert code == 2
    assert "ERROR:" in capsys.readouterr().err


def test_default_contracts_file_prefers_repo_layout(tmp_path: Path) -> None:
    repo_file = tmp_path / ".claude" / "sdd" / "architecture" / "WORKFLOW_CONTRACTS.yaml"
    repo_file.parent.mkdir(parents=True)
    repo_file.write_text("{}")
    assert cli._resolve_default_contracts_file(tmp_path) == repo_file


def test_default_contracts_file_falls_back_to_plugin_layout(tmp_path: Path) -> None:
    # No .claude/ prefix — this is the installed-plugin layout (the fixed bug).
    plugin_file = tmp_path / "sdd" / "architecture" / "WORKFLOW_CONTRACTS.yaml"
    plugin_file.parent.mkdir(parents=True)
    plugin_file.write_text("{}")
    assert cli._resolve_default_contracts_file(tmp_path) == plugin_file
