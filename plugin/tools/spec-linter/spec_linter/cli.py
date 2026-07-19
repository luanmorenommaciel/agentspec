"""CLI: `python -m spec_linter.cli [path] [--phase NAME] [--emit-schema OUT.json]`.

Lints a spec file — a YAML mapping, or a self-contained `.md` whose leading
YAML frontmatter IS the spec — or a directory of specs, against the baked-in
agent-spec contract; or (with `--phase`) a Markdown phase document against an
`SddPhaseContract`. The CLI is a consumer of the engine and owns the usage
policy: YAML/frontmatter/Markdown loading, directory iteration, the
cross-file duplicate-id (L4) check, and contract selection.

Exit codes form a three-way contract:

- 0 — PASS or WARN verdict.
- 1 — FAIL verdict (a loadable artifact that violates its contract).
- 2 — ERROR: an operational failure (file not found, YAML syntax error, a
  non-mapping top level, a `.md` file with no frontmatter or an invalid/
  non-mapping frontmatter block, an unknown phase, or any unexpected
  exception). ERROR is a process concern only — it is NOT a Verdict Level;
  the Verdict surface stays exactly PASS/WARN/FAIL.
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
from .frontmatter import FrontmatterError, split_frontmatter
from .verdict import Level, Verdict

_CONTRACT = AgentSpecContract()

# Tool-root-relative default; the CLI lives at tools/spec-linter/spec_linter/cli.py.
def _resolve_default_contracts_file(tool_root: Path) -> Path:
    """Probe both layouts and return the first that exists.

    A repo checkout nests the file under `.claude/`; the installed plugin does
    not (its root already is the former `.claude/`). Falls back to the repo
    layout so a genuinely missing file still degrades loudly (exit 2) with an
    informative path instead of silently picking a nonexistent default.
    """
    repo_layout = tool_root / ".claude" / "sdd" / "architecture" / "WORKFLOW_CONTRACTS.yaml"
    plugin_layout = tool_root / "sdd" / "architecture" / "WORKFLOW_CONTRACTS.yaml"
    return next((p for p in (repo_layout, plugin_layout) if p.exists()), repo_layout)


_DEFAULT_CONTRACTS_FILE = _resolve_default_contracts_file(Path(__file__).resolve().parents[3])


class _OperationalError(Exception):
    """Raised for failures that must map to exit code 2 (ERROR), not a verdict."""


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a YAML mapping at the top level")
    return data


def _load_md_frontmatter(path: Path) -> dict[str, Any]:
    """Load a `.md` file's leading YAML frontmatter as the spec mapping.

    The frontmatter IS the spec for a self-contained agent `.md` file. No
    frontmatter block, or a present-but-invalid one, is an operational
    failure (exit 2) — never a silent pass.
    """
    text = path.read_text(encoding="utf-8")
    try:
        frontmatter, _ = split_frontmatter(text)
    except FrontmatterError as exc:
        raise _OperationalError(f"{path.name}: {exc}") from exc
    if frontmatter is None:
        raise _OperationalError(f"{path.name}: no YAML frontmatter block found")
    return frontmatter


def _load_spec(path: Path) -> dict[str, Any]:
    """Load a spec mapping from `path`: `.md` frontmatter, or a YAML mapping."""
    return _load_md_frontmatter(path) if path.suffix == ".md" else _load_yaml(path)


def _lint_file(path: Path) -> Verdict:
    """Lint one spec file against the agent-spec contract.

    `.yaml`/`.yml` are loaded as a plain YAML mapping. `.md` is treated as a
    self-contained artifact: its leading YAML frontmatter IS the spec (see
    `frontmatter.split_frontmatter`) — everything else about the file body is
    irrelevant to the contract check.
    """
    return lint(_load_spec(path), _CONTRACT)


_SKIP_EXACT_NAMES = frozenset({"README.md"})


def _is_spec_skip(name: str) -> bool:
    """Non-spec files the directory walk excludes: `_`-prefixed, or `README.md`."""
    return name.startswith("_") or name in _SKIP_EXACT_NAMES


def _lint_dir(path: Path) -> dict[str, Verdict]:
    """Lint every `.yaml`/`.yml`/`.md` spec file under `path`, keyed by its
    path relative to it.

    Walks subdirectories, so a category tree (e.g. `plugin/agents/<pod>/*.md`)
    lints as one fleet in a single run. Files named exactly `README.md`, or
    whose name starts with `_` (scaffolding/templates), are excluded from
    linting; they are reported once in a single summary line so the exclusion
    is visible, never silent.

    Adds the cross-file duplicate-id (L4) check on top of the per-file
    verdicts, spanning YAML and MD sources alike: a duplicated id appends the
    same finding to every file that claims it.
    """
    candidates = sorted(
        p for p in path.rglob("*") if p.is_file() and p.suffix in (".yaml", ".yml", ".md")
    )
    selected = [p for p in candidates if not _is_spec_skip(p.name)]
    skipped = [p for p in candidates if _is_spec_skip(p.name)]
    if skipped:
        names = ", ".join(sorted(str(p.relative_to(path)) for p in skipped))
        print(f"skipped (non-spec): {names}")

    verdicts: dict[str, Verdict] = {}
    ids_by_source: dict[str, list[str]] = {}
    for file in selected:
        label = str(file.relative_to(path))
        data = _load_spec(file)
        verdicts[label] = lint(data, _CONTRACT)
        spec_id = data.get("id")
        if isinstance(spec_id, str):
            ids_by_source.setdefault(spec_id, []).append(label)
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
