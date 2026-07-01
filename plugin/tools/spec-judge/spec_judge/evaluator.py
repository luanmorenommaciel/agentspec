"""Evaluation data shapes + a deterministic fake evaluator.

An ``Evaluator`` turns an ``EvalRequest`` (role + artifact + contract summary +
rubric) into an ``EvalResult`` (concerns + confidence). The real one calls a model
(``openrouter.py``); ``FakeEvaluator`` is scripted, for deterministic tests.

The evaluator reports concerns and a confidence — it does **not** emit a verdict.
Turning concerns into a ``PASS | WARN | FAIL`` verdict is the engine's job
(``consensus.py``), so verdict policy lives in exactly one place.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict

from .contracts import Rubric
from .vocab import Category, Role, Severity


class Concern(BaseModel):
    """One behavioral defect an evaluator raises. Maps onto the Linter's ``Finding``."""

    model_config = ConfigDict(frozen=True)

    category: Category
    severity: Severity
    evidence: str  # quoted artifact text          -> Finding.found
    expected: str  # what the contract required     -> Finding.expected
    recommendation: str  # the concrete fix         -> folded into Finding.message


class EvalRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Role
    artifact_text: str
    contract_summary: str
    rubric: Rubric
    model: str | None = None  # None -> the evaluator's default model
    cross_model: bool = False  # True marks the deliberately different-model seat
    peer_concerns: tuple[Concern, ...] = ()  # only the arbiter receives these


class EvalResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Role
    model: str
    cross_model: bool = False
    confidence: float  # 0.0-1.0
    summary: str = ""
    concerns: tuple[Concern, ...] = ()
    raw: dict[str, Any] | None = None  # the raw model JSON, for debugging


class FakeEvaluator:
    """Deterministic evaluator for tests: a ``(request) -> EvalResult`` function.

    The panel constructs one evaluator and calls it once per seat, so the script
    branches on ``request.role`` / ``request.cross_model`` to return per-seat results.
    """

    name = "fake"

    def __init__(self, script: Callable[[EvalRequest], EvalResult]) -> None:
        self._script = script

    def evaluate(self, request: EvalRequest) -> EvalResult:
        return self._script(request)
