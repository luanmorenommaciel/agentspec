"""Behavioral evaluation engine (the Judger) — the model-based counterpart to the
deterministic Linter.

Entry point: ``from spec_judge.engine import judge``. ``judge(artifact, contract, panel)
-> Verdict`` returns the SAME ``Verdict`` the Linter returns (``from spec_linter import
Verdict, Finding, Level``), so a consumer handles the structural and behavioral gates
with one code path.

This ``__init__`` re-exports only names that do NOT import the sibling ``spec_linter`` at
import time, so the ``--selfcheck`` / ``--ledger`` CLI paths keep working even when the
sibling is momentarily unresolved. The engine/verdict live one import away by design.
"""

from __future__ import annotations

from .contracts import EvalSubject, Rubric, SpecConformanceContract, split_frontmatter
from .evaluator import Concern, EvalRequest, EvalResult, FakeEvaluator
from .panel import Panel, Seat
from .protocol import BehavioralContract, Evaluator

__all__ = [
    "BehavioralContract",
    "Concern",
    "EvalRequest",
    "EvalResult",
    "EvalSubject",
    "Evaluator",
    "FakeEvaluator",
    "Panel",
    "Rubric",
    "Seat",
    "SpecConformanceContract",
    "split_frontmatter",
]
