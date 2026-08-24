"""CLI: `python -m spec_composer.cli [spec] --out PATH [--pipeline PATH]`.

Drives one artifact through a pipeline contract, or validates a contract without
running it (`--check`), or reports whether the sibling components resolve
(`--selfcheck`).

Exit codes — the VERDICT surface stays PASS/WARN/FAIL and belongs to the gates.
These five codes are the RUN's disposition; any code >= 2 means no verdict was
reached and must never be read as PASS:

  0  EMITTED — every declared stage cleared and the artifact was promoted
  1  BLOCKED — budget exhausted on a gate FAIL, or a high-assurance judge FAIL
  2  ERROR   — operational failure (bad contract, unresolvable reference, missing
               spec, bad archive template, failed promotion, unparseable judge
               subject, sibling linter absent)
  3  PAUSED  — a bound stage could not run, or an approval is outstanding
  4  WAITING — a producing stage has no usable output for this attempt; re-run

`--check` is a different surface and follows the Linter's contract exactly:
0 PASS/WARN, 1 FAIL, 2 unloadable.

Engine imports are deferred until after `--selfcheck` so that mode reports a
clean error even when the sibling `spec_linter` cannot be found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .models import ComposeResult

_EXIT_BY_DISPOSITION = {
    "emitted": 0,
    "blocked": 1,
    "error": 2,
    "paused": 3,
    "waiting": 4,
}


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="spec_composer",
        description="AgentSpec artifact-creation conductor (the Composer).",
    )
    parser.add_argument(
        "spec", nargs="?", help="creation spec, or the pipeline contract with --check"
    )
    parser.add_argument(
        "--out", metavar="PATH", type=Path, help="emit target for the produced artifact"
    )
    parser.add_argument(
        "--pipeline",
        metavar="PATH",
        type=Path,
        help="pipeline contract to run (default: the shipped agent-creation one)",
    )
    parser.add_argument(
        "--approve",
        metavar="CLASS",
        action="append",
        default=[],
        help="grant an approval class named by require_approval_for (repeatable)",
    )
    parser.add_argument(
        "--check", action="store_true", help="validate a pipeline contract without running it"
    )
    parser.add_argument("--json", action="store_true", help="emit the run result as JSON")
    parser.add_argument(
        "--selfcheck", action="store_true", help="verify the sibling components resolve, then exit"
    )
    args = parser.parse_args(argv)
    if args.check and args.spec is None:
        parser.error("--check needs the path of the pipeline contract to validate")
    return args


def _selfcheck() -> int:
    try:
        from spec_linter import Finding, Level, Verdict, lint  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        print(
            f"ERROR: cannot import spec_linter (sibling component missing): {exc}", file=sys.stderr
        )
        return 2
    try:
        import spec_judge  # noqa: F401
    except Exception:  # noqa: BLE001
        print(
            "ok: spec-compose ready (spec_linter resolves; spec_judge absent — "
            "a judge stage will pause rather than be skipped)"
        )
        return 0
    print("ok: spec-compose ready (spec_linter and spec_judge resolve)")
    return 0


def _default_pipeline_path() -> Path:
    """The shipped pipeline, resolved from the tool root."""
    return Path(__file__).resolve().parents[1] / "pipelines" / "agent-creation.yaml"


def _load_contract(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"pipeline contract not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    raise ValueError(f"{path.name}: expected a YAML mapping at the top level")


def _result_to_json(result: ComposeResult) -> dict[str, Any]:
    """Levels render as names — a bare `model_dump` would emit the raw IntEnum."""
    return {
        "disposition": result.disposition.value,
        "stage": result.stage,
        "reason": result.reason,
        "epoch": result.epoch,
        "attempt": result.attempt,
        "attempts_spent": result.attempts_spent,
        "artifact": str(result.artifact) if result.artifact else None,
        "expected_path": str(result.expected_path) if result.expected_path else None,
        "run_dir": str(result.run_dir),
        "trail": [
            {
                "stage": entry.stage,
                "kind": entry.stage_kind,
                "contract": entry.contract,
                "attempt": entry.attempt,
                "level": entry.verdict.level.name,
                "findings": [
                    {**finding.model_dump(mode="json"), "level": finding.level.name}
                    for finding in entry.verdict.findings
                ],
            }
            for entry in result.trail
        ],
    }


def _emit(result: ComposeResult, as_json: bool) -> None:
    """Human surface: the verdict trail in the Linter's rendering, then the
    disposition WITH its reason, then whatever the operator has to do next."""
    if as_json:
        print(json.dumps(_result_to_json(result), indent=2))
        return
    for entry in result.trail:
        print(f"== {entry.stage} ({entry.contract}) ==")
        print(entry.verdict)
    suffix = f" ({result.reason})" if result.reason else ""
    print(f"DISPOSITION: {result.disposition.value.upper()}{suffix}")
    if result.expected_path is not None:
        print(f"  expected at: {result.expected_path}")
    if result.artifact is not None:
        print(f"  emitted to: {result.artifact}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.selfcheck:
        return _selfcheck()

    contract_path = Path(args.spec) if args.check else (args.pipeline or _default_pipeline_path())
    try:
        document = _load_contract(contract_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        from spec_linter import Level, lint

        from .contract import PipelineContract, PipelineSpec
    except ImportError as exc:
        print(
            f"ERROR: cannot import spec_linter (sibling component missing): {exc}", file=sys.stderr
        )
        return 2

    verdict = lint(document, PipelineContract())
    if args.check:
        print(f"== {contract_path.name} (pipeline contract) ==")
        print(verdict)
        return 1 if verdict.level is Level.FAIL else 0
    if verdict.level is Level.FAIL:
        print(f"ERROR: pipeline contract {contract_path} is invalid", file=sys.stderr)
        print(verdict, file=sys.stderr)
        return 2

    if args.out is None:
        print("ERROR: --out is required for a run", file=sys.stderr)
        return 2
    spec_path = Path(args.spec).expanduser() if args.spec else None
    if spec_path is not None and not spec_path.exists():
        print(f"ERROR: spec not found: {spec_path}", file=sys.stderr)
        return 2

    from .emit import EmitError
    from .engine import compose
    from .judging import JudgeUnavailable
    from .models import ComposeRequest
    from .resolver import UnresolvedContract

    target = args.out.expanduser()
    request = ComposeRequest(
        name=target.stem, target=target, spec_path=spec_path, approvals=frozenset(args.approve)
    )
    try:
        result = compose(request, PipelineSpec.from_mapping(document))
    except (UnresolvedContract, EmitError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except JudgeUnavailable as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: unexpected failure: {exc}", file=sys.stderr)
        return 2

    _emit(result, args.json)
    return _EXIT_BY_DISPOSITION[result.disposition.value]


if __name__ == "__main__":
    sys.exit(main())
