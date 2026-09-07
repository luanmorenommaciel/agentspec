"""CLI: exit-code contract (0 = scored, 2 = error) and output."""

from __future__ import annotations

import textwrap

import yaml

from spec_scorer.cli import main


def _write_md_spec(path, spec: dict) -> None:
    path.write_text(f"---\n{yaml.safe_dump(spec)}---\n\n# Body\n", encoding="utf-8")


def test_scores_yaml_spec(tmp_path, valid_spec, capsys) -> None:
    f = tmp_path / "agent.yaml"
    f.write_text(yaml.safe_dump(valid_spec), encoding="utf-8")
    assert main([str(f)]) == 0
    out = capsys.readouterr().out
    assert "SCORECARD" in out
    assert "maturity_conformance" in out


def test_scores_md_frontmatter_spec(tmp_path, valid_spec, capsys) -> None:
    f = tmp_path / "agent.md"
    _write_md_spec(f, valid_spec)
    assert main([str(f)]) == 0
    assert "SCORECARD" in capsys.readouterr().out


def test_missing_file_is_error(tmp_path, capsys) -> None:
    assert main([str(tmp_path / "nope.yaml")]) == 2
    assert "ERROR" in capsys.readouterr().err


def test_unparseable_spec_is_error(tmp_path, valid_spec, capsys) -> None:
    del valid_spec["maturity"]
    f = tmp_path / "agent.yaml"
    f.write_text(yaml.safe_dump(valid_spec), encoding="utf-8")
    assert main([str(f)]) == 2
    assert "ERROR" in capsys.readouterr().err


def test_md_without_frontmatter_is_error(tmp_path, capsys) -> None:
    f = tmp_path / "agent.md"
    f.write_text("# Just a heading, no frontmatter\n", encoding="utf-8")
    assert main([str(f)]) == 2


def test_kb_index_enables_reference_integrity(tmp_path, valid_spec, capsys) -> None:
    index = tmp_path / "_index.yaml"
    index.write_text(
        textwrap.dedent(
            """
            domains:
              testing:
                name: testing
              python:
                name: python
            """
        ),
        encoding="utf-8",
    )
    f = tmp_path / "agent.yaml"
    f.write_text(yaml.safe_dump(valid_spec), encoding="utf-8")
    assert main([str(f), "--kb-index", str(index)]) == 0
    assert "reference_integrity" in capsys.readouterr().out
