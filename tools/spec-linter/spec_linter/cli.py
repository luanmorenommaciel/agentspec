"""CLI: `python -m spec_linter.cli <path> [--emit-schema OUT.json]`.

Lints a file or a directory; exits 1 if any verdict is FAIL, else 0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .contracts.agent_spec import emit_json_schema
from .linter import lint_dir, lint_file
from .verdict import Level, Verdict


def _write_schema(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(emit_json_schema(), indent=2) + "\n")
    print(f"Wrote JSON Schema to {out}")


def _lint_path(path: Path) -> Level:
    if path.is_dir():
        verdicts = lint_dir(path)
        worst = Level.PASS
        for name, verdict in verdicts.items():
            print(f"== {name} ==")
            print(verdict)
            print()
            worst = max(worst, verdict.level)
        print(f"OVERALL: {worst.name}")
        return worst

    verdict: Verdict = lint_file(path)
    print(f"== {path.name} ==")
    print(verdict)
    return verdict.level


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="spec_linter", description="AgentSpec contract-validation engine (the Linter)."
    )
    parser.add_argument("path", nargs="?", help="spec file or directory to lint")
    parser.add_argument(
        "--emit-schema",
        metavar="OUT.json",
        type=Path,
        help="write the spec JSON Schema to OUT.json and exit",
    )
    args = parser.parse_args(argv)

    if args.emit_schema is not None:
        _write_schema(args.emit_schema)
        if args.path is None:
            return 0

    if args.path is None:
        parser.error("a path is required unless only --emit-schema is given")

    level = _lint_path(Path(args.path))
    return 1 if level == Level.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
