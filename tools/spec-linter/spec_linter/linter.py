"""Gate A orchestration: run L1-L4 and produce a Verdict.

Pipeline per spec:
  L1  Pydantic validation  -> AgentSpec  (or FAIL findings on ValidationError)
  L1  unknown-field scan    -> WARN findings
  L2  governance rules
  L3  consistency rules
Directory lint additionally runs L4 (duplicate id across files).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from . import rules
from .models import AgentSpec
from .verdict import Finding, Level, Verdict


def emit_json_schema() -> dict[str, Any]:
    """The same Pydantic model that validates specs also emits the JSON Schema."""
    return AgentSpec.model_json_schema()


def _l1_findings(error: ValidationError) -> list[Finding]:
    """One FAIL finding per Pydantic error, carrying the field path and message."""
    findings: list[Finding] = []
    for err in error.errors():
        field = ".".join(str(part) for part in err["loc"]) or None
        findings.append(
            Finding(
                level=Level.FAIL,
                rule="L1.schema",
                field=field,
                message=err["msg"],
                found=err["type"],
            )
        )
    return findings


def lint_spec(data: dict[str, Any]) -> Verdict:
    """Lint a single already-parsed spec mapping (L1-L3)."""
    try:
        spec = AgentSpec.model_validate(data)
    except ValidationError as exc:
        return Verdict.from_findings(_l1_findings(exc))

    findings = rules.unknown_field_findings(spec)
    findings += rules.l2_governance_findings(spec)
    findings += rules.l3_consistency_findings(spec)
    return Verdict.from_findings(findings)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a YAML mapping at the top level")
    return data


def lint_file(path: str | Path) -> Verdict:
    """Lint a single YAML file. L4 is skipped (needs a directory)."""
    return lint_spec(_load_yaml(Path(path)))


def lint_dir(path: str | Path) -> dict[str, Verdict]:
    """Lint every *.yaml/*.yml in a directory and apply L4 across them.

    Returns a mapping of file name -> Verdict. The L4 duplicate-id findings are
    appended to the verdict of every file that participates in a collision.
    """
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
            new = Verdict.from_findings([*verdict.findings, finding])
            verdicts[source] = new

    return verdicts
