"""CLI: ``python -m spec_scorer.cli <path> [--kb-index PATH]``.

Scores an agent spec — a YAML mapping, or a self-contained `.md` whose leading
YAML frontmatter IS the spec — against the baked-in agent-spec scoring contract,
and prints a ScoreCard. With `--kb-index`, the reference_integrity dimension is
enabled by loading the known KB-domain set from a `_index.yaml`.

Exit codes — the Scorer is **analytical, not a gate**, so there is no FAIL code;
a low score is a normal, successful result:

  0  SCORED — a ScoreCard was produced (whatever the scores are)
  2  ERROR  — operational failure (missing/empty file, no frontmatter, a
             non-mapping top level, an unparseable spec, a bad --kb-index)

A consumer never blocks on the exit code; it reads the ScoreCard. Exit 2 means
"could not measure", never "measured badly".
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from .contracts import AgentSpecScoringContract
from .engine import score


class _OperationalError(Exception):
    """A failure that maps to exit code 2 (ERROR), not a ScoreCard."""


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise _OperationalError(f"{path.name}: expected a YAML mapping at the top level")
    return data


def _load_md_frontmatter(path: Path) -> dict[str, Any]:
    from spec_linter.frontmatter import FrontmatterError, split_frontmatter

    try:
        frontmatter, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    except FrontmatterError as exc:
        raise _OperationalError(f"{path.name}: {exc}") from exc
    if frontmatter is None:
        raise _OperationalError(f"{path.name}: no YAML frontmatter block found")
    return frontmatter


def _load_spec(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".md":
        return _load_md_frontmatter(path)
    return _load_yaml(path)


def _load_known_kb_domains(index_path: Path) -> set[str]:
    """The set of KB-domain names from a `_index.yaml` `domains:` mapping."""
    if not index_path.exists():
        raise _OperationalError(f"kb index not found: {index_path}")
    try:
        data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise _OperationalError(f"could not parse kb index {index_path}: {exc}") from exc
    domains = (data or {}).get("domains")
    if not isinstance(domains, dict):
        raise _OperationalError(f"{index_path.name}: no `domains` mapping found")
    known = set(domains.keys())
    shared = (data or {}).get("shared")
    if shared is not None:
        known.add("shared")
    return known


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="spec_scorer", description="AgentSpec artifact scoring engine (the Scorer)."
    )
    parser.add_argument("path", help="agent spec file (.yaml/.yml or .md frontmatter)")
    parser.add_argument(
        "--kb-index",
        metavar="PATH",
        type=Path,
        help="a KB _index.yaml; enables the reference_integrity dimension",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="expand each dimension into its per-topic checkpoints (✓/✗ and +N)",
    )
    args = parser.parse_args(argv)

    try:
        path = Path(args.path)
        if not path.exists():
            raise _OperationalError(f"file not found: {path}")
        spec = _load_spec(path)
        known = _load_known_kb_domains(args.kb_index) if args.kb_index else None
        contract = AgentSpecScoringContract(known_kb_domains=known)
        card = score(spec, contract)
    except _OperationalError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # unparseable spec or any unexpected failure -> ERROR
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"== {path.name} ==")
    print(card.render(explain=args.explain))
    return 0


if __name__ == "__main__":
    sys.exit(main())
