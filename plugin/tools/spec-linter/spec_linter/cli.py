"""CLI: `python -m spec_linter.cli [path] [--phase NAME] [--emit-schema OUT.json]`.

Lints a spec file or a directory of specs against the baked-in agent-spec
contract, or (with `--phase`) a Markdown phase document against an
`SddPhaseContract`. The CLI is a consumer of the engine and owns the usage
policy: YAML/Markdown loading, directory iteration, the cross-file duplicate-id
(L4) check, and contract selection.

Exit codes form a three-way contract:

- 0 — PASS or WARN verdict.
- 1 — FAIL verdict (a loadable artifact that violates its contract).
- 2 — ERROR: an operational failure (file not found, YAML syntax error, a
  non-mapping top level, an unknown phase, or any unexpected exception). ERROR
  is a process concern only — it is NOT a Verdict Level; the Verdict surface
  stays exactly PASS/WARN/FAIL.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from . import rules
from .contracts.agent_spec import AgentSpecContract, emit_json_schema
from .contracts.sdd_phase import SddPhaseContract
from .engine import lint
from .verdict import Level, Verdict

_CONTRACT = AgentSpecContract()

# Repo-root-relative default; the CLI lives at tools/spec-linter/spec_linter/cli.py.
_DEFAULT_CONTRACTS_FILE = (
    Path(__file__).resolve().parents[3]
    / ".claude"
    / "sdd"
    / "architecture"
    / "WORKFLOW_CONTRACTS.yaml"
)


class _OperationalError(Exception):
    """Raised for failures that must map to exit code 2 (ERROR), not a verdict."""


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a YAML mapping at the top level")
    return data


def _lint_file(path: Path) -> Verdict:
    """Lint one YAML spec file against the agent-spec contract."""
    return lint(_load_yaml(path), _CONTRACT)


def _lint_dir(path: Path) -> dict[str, Verdict]:
    """Lint every `.yaml`/`.yml` file in a directory, keyed by file name.

    Adds the cross-file duplicate-id (L4) check on top of the per-file
    verdicts: a duplicated id appends the same finding to every file that
    claims it.
    """
    files = sorted(p for p in path.iterdir() if p.suffix in (".yaml", ".yml"))
    verdicts: dict[str, Verdict] = {}
    ids_by_source: dict[str, list[str]] = {}
    for file in files:
        data = _load_yaml(file)
        verdicts[file.name] = lint(data, _CONTRACT)
        spec_id = data.get("id")
        if isinstance(spec_id, str):
            ids_by_source.setdefault(spec_id, []).append(file.name)
    for spec_id, sources in ids_by_source.items():
        for finding in rules.l4_identity_findings({spec_id: sources}):
            for source in sources:
                verdicts[source] = Verdict.from_findings([*verdicts[source].findings, finding])
    return verdicts


def _phase_required_sections(phase: str, contracts_file: Path) -> list[str]:
    """Read a phase's `required_sections` from a WORKFLOW_CONTRACTS-style YAML."""
    if not contracts_file.exists():
        raise _OperationalError(f"contracts file not found: {contracts_file}")
    try:
        data = yaml.safe_load(contracts_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise _OperationalError(f"could not parse contracts file {contracts_file}: {exc}") from exc
    block = (data or {}).get(phase)
    if not isinstance(block, dict) or "required_sections" not in block:
        raise _OperationalError(
            f"phase '{phase}' has no required_sections in {contracts_file.name}"
        )
    sections = block["required_sections"]
    if not isinstance(sections, list) or not all(isinstance(s, str) for s in sections):
        raise _OperationalError(f"phase '{phase}' required_sections must be a list of strings")
    return sections


def _lint_phase(path: Path, phase: str, contracts_file: Path) -> Level:
    """Lint a Markdown phase document against its phase contract."""
    required = _phase_required_sections(phase, contracts_file)
    contract = SddPhaseContract(phase, required)
    verdict = lint(path.read_text(encoding="utf-8"), contract)
    print(f"== {path.name} (phase: {phase}) ==")
    print(verdict)
    return verdict.level


def _write_schema(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(emit_json_schema(), indent=2) + "\n")
    print(f"Wrote JSON Schema to {out}")


def _lint_path(path: Path) -> Level:
    if path.is_dir():
        verdicts = _lint_dir(path)
        worst = Level.PASS
        for name, verdict in verdicts.items():
            print(f"== {name} ==")
            print(verdict)
            print()
            worst = max(worst, verdict.level)
        print(f"OVERALL: {worst.name}")
        return worst

    verdict = _lint_file(path)
    print(f"== {path.name} ==")
    print(verdict)
    return verdict.level


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="spec_linter", description="AgentSpec contract-validation engine (the Linter)."
    )
    parser.add_argument("path", nargs="?", help="spec file/dir, or phase document with --phase")
    parser.add_argument(
        "--phase",
        metavar="NAME",
        help="lint PATH as a Markdown phase document against the named phase contract",
    )
    parser.add_argument(
        "--contracts-file",
        metavar="PATH",
        type=Path,
        default=_DEFAULT_CONTRACTS_FILE,
        help="WORKFLOW_CONTRACTS-style YAML source for --phase required_sections",
    )
    parser.add_argument(
        "--emit-schema",
        metavar="OUT.json",
        type=Path,
        help="write the spec JSON Schema to OUT.json",
    )
    args = parser.parse_args(argv)

    if args.emit_schema is not None:
        _write_schema(args.emit_schema)
        if args.path is None:
            return 0

    if args.path is None:
        parser.error("a path is required unless only --emit-schema is given")

    try:
        if args.phase is not None:
            level = _lint_phase(Path(args.path), args.phase, args.contracts_file)
        else:
            level = _lint_path(Path(args.path))
    except FileNotFoundError as exc:
        print(f"ERROR: file not found: {exc.filename or args.path}", file=sys.stderr)
        return 2
    except (yaml.YAMLError, ValueError, _OperationalError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # operational failure, not a verdict
        print(f"ERROR: unexpected failure: {exc}", file=sys.stderr)
        return 2

    return 1 if level == Level.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
