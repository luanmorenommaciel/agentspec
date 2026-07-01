"""CLI: ``python -m spec_judge.cli <artifact> [--spec SPEC] [--tier TIER] ...``

Behavioral evaluation of a produced artifact against its source spec. Runs a tiered
adversarial panel and prints a ``PASS | WARN | FAIL`` verdict.

Exit codes — the *verdict* surface stays PASS/WARN/FAIL (codes 0/1). Codes 2/3/4 are
NOT verdicts: they are "couldn't-run" states. A consumer treats any code ``>= 2`` as
"skip the behavioral check visibly and proceed" (never assume PASS), or branches on
the specific code:

  0  PASS or WARN — proceed
  1  FAIL — a high-assurance blocking verdict
  2  ERROR — operational failure (missing/empty artifact, no source spec, bad config)
  3  BUDGET — the per-day evaluation budget is exhausted
  4  NETWORK — model/API failure

The engine imports are deferred until after ``--selfcheck``/``--ledger`` so those can
run (and report a clean error) even when the sibling ``spec_linter`` cannot be found.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from .contracts import split_frontmatter

TIERS = ("smoke", "standard", "high-assurance")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="spec_judge", description="AgentSpec behavioral evaluation engine (the Judger)."
    )
    parser.add_argument("artifact", nargs="?", help="path to the produced artifact to judge")
    parser.add_argument(
        "--spec",
        type=Path,
        help="source spec (YAML). If omitted, the artifact's own frontmatter is used as its spec.",
    )
    parser.add_argument("--tier", choices=TIERS, default="standard", help="independence tier")
    parser.add_argument("--model", help="override the model for same-platform seats")
    parser.add_argument("--alt-model", help="override the cross-model seat (high-assurance tier)")
    parser.add_argument("--json", action="store_true", help="emit the verdict as JSON")
    parser.add_argument("--ledger", action="store_true", help="show today's budget usage and exit")
    parser.add_argument(
        "--selfcheck",
        action="store_true",
        help="verify the sibling spec_linter resolves, then exit",
    )
    return parser.parse_args(argv)


def _selfcheck() -> int:
    try:
        from spec_linter import Finding, Level, Verdict  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        print(
            f"ERROR: cannot import spec_linter (sibling component missing): {exc}", file=sys.stderr
        )
        return 2
    print("ok: spec-judge ready (spec_linter resolves)")
    return 0


def _show_ledger() -> int:
    from . import ledger

    print(f"Judge ledger — {ledger.ledger_path()}")
    print(f"  Today: {ledger.today_count()} / {ledger.budget()} calls")
    return 0


def _load_spec_and_body(args: argparse.Namespace, artifact_text: str) -> tuple[dict[str, Any], str]:
    """Resolve (source_spec, body). Raises ValueError with an operator message on failure."""
    if args.spec is not None:
        if not args.spec.exists():
            raise ValueError(f"spec not found: {args.spec}")
        try:
            spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"could not parse spec YAML: {exc}") from exc
        body = artifact_text
    else:
        spec, body = split_frontmatter(artifact_text)
        if spec is None:
            raise ValueError(
                "no --spec given and the artifact has no YAML frontmatter to use as its spec"
            )
    if not isinstance(spec, dict):
        raise ValueError("the source spec must be a YAML mapping")
    if not body.strip():
        raise ValueError("artifact body is empty — nothing to judge")
    return spec, body


def _build_panel(args: argparse.Namespace):
    from .openrouter import OpenRouterEvaluator
    from .panel import DEFAULT_ALT_MODEL, Panel

    evaluator = OpenRouterEvaluator(default_model=args.model) if args.model else None
    if args.tier == "high-assurance":
        return Panel.high_assurance(
            evaluator=evaluator, alt_model=args.alt_model or DEFAULT_ALT_MODEL
        )
    return Panel.for_tier(args.tier, evaluator=evaluator)


def _emit(verdict: object, as_json: bool) -> None:
    if as_json:
        import json

        print(json.dumps(verdict.model_dump(mode="json"), indent=2))  # type: ignore[attr-defined]
    else:
        print(verdict)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.selfcheck:
        return _selfcheck()
    if args.ledger:
        return _show_ledger()

    if not args.artifact:
        print("ERROR: an artifact path is required", file=sys.stderr)
        return 2
    artifact_path = Path(args.artifact).expanduser()
    if not artifact_path.exists():
        print(f"ERROR: artifact not found: {artifact_path}", file=sys.stderr)
        return 2
    artifact_text = artifact_path.read_text(encoding="utf-8", errors="replace")

    try:
        spec, body = _load_spec_and_body(args, artifact_text)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    from .contracts import SpecConformanceContract
    from .engine import judge
    from .ledger import BudgetError, preflight
    from .openrouter import ConfigError, NetworkError

    try:
        panel = _build_panel(args)
        preflight(len(panel.seats))
        verdict = judge(body, SpecConformanceContract(spec), panel)
    except BudgetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    except NetworkError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 4
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    _emit(verdict, args.json)
    from spec_linter import Level

    return 1 if verdict.level == Level.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
