"""The behavioral seam — bound lazily so the Judger stays optional.

`spec_judge` is imported INSIDE the call, never at module import time: contract
checking, a judge-less pipeline and `--selfcheck` must all work with the sibling
absent. Every could-not-run cause raises `JudgeUnavailableError`, which the conductor
turns into a pause — unavailability never equals PASS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from spec_linter import Verdict

if TYPE_CHECKING:
    from spec_judge import Evaluator


class JudgeUnavailableError(RuntimeError):
    """A bound judge stage could not be run. Never a verdict."""


def judge_artifact(
    artifact_text: str,
    source_spec: dict[str, Any],
    *,
    tier: str,
    evaluator: Evaluator | None = None,
) -> Verdict:
    try:
        from spec_judge.contracts import SpecConformanceContract, split_frontmatter
        from spec_judge.engine import judge
        from spec_judge.ledger import BudgetError, preflight
        from spec_judge.openrouter import ConfigError, NetworkError
        from spec_judge.panel import Panel
    except ImportError as exc:
        raise JudgeUnavailableError(
            f"the behavioral evaluation engine is unavailable: {exc}"
        ) from exc

    _, body = split_frontmatter(artifact_text)
    try:
        panel = Panel.for_tier(tier, evaluator=evaluator)
        preflight(len(panel.seats))
        return judge(body or artifact_text, SpecConformanceContract(source_spec), panel)
    except (BudgetError, NetworkError, ConfigError) as exc:
        raise JudgeUnavailableError(str(exc)) from exc
