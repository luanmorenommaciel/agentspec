"""Compatibility surface over the engine + agent-spec reference contract.

Pre-refactor callers used lint_spec/lint_file/lint_dir and emit_json_schema
from here. These now delegate to engine.lint() with the AgentSpecContract so
the public behavior is preserved while the mechanism/policy split lives in
engine.py + contracts/.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from . import rules
from .contracts.agent_spec import AgentSpecContract, emit_json_schema  # re-export
from .engine import lint
from .verdict import Verdict

__all__ = ["lint_spec", "lint_file", "lint_dir", "emit_json_schema"]

_CONTRACT = AgentSpecContract()


def lint_spec(data: dict[str, Any]) -> Verdict:
    return lint(data, _CONTRACT)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{Path(path).name}: expected a YAML mapping at the top level")
    return data


def lint_file(path: str | Path) -> Verdict:
    return lint_spec(_load_yaml(Path(path)))


def lint_dir(path: str | Path) -> dict[str, Verdict]:
    directory = Path(path)
    files = sorted(p for p in directory.iterdir() if p.suffix in (".yaml", ".yml"))
    verdicts: dict[str, Verdict] = {}
    ids_by_source: dict[str, list[str]] = {}
    for file in files:
        verdicts[file.name] = lint_file(file)
        try:
            spec_id = _load_yaml(file).get("id")
        except ValueError:
            spec_id = None
        if isinstance(spec_id, str):
            ids_by_source.setdefault(spec_id, []).append(file.name)
    for finding in rules.l4_identity_findings(ids_by_source):
        for source in (finding.found or "").split(", "):
            verdict = verdicts[source]
            verdicts[source] = Verdict.from_findings([*verdict.findings, finding])
    return verdicts
