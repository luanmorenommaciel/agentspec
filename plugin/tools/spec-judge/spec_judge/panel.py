"""The panel — tiered adversarial seats and a flat evaluation loop.

A ``Seat`` is ``(role, model, cross_model)``. A ``Panel`` holds its tier, its seats,
and the injected evaluator (the real ``OpenRouterEvaluator`` unless a fake is passed).
``evaluate`` runs the seats in order; the arbiter — always last — receives the prior
seats' concerns so it can adjudicate them.

Independence is dialed by tier, with one invariant in every tier: at least one
fault-seeker (a seat tasked to find where the artifact fails its contract). The
high-assurance tier adds a *second* fault-seeker on a deliberately different model,
flagged ``cross_model`` so consensus can require genuine cross-model agreement.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict

from .contracts import EvalSubject, Rubric
from .evaluator import EvalRequest, EvalResult
from .protocol import Evaluator
from .vocab import Role

# The canonical independence tiers, shared by the CLI (argument choices) and
# consensus.py (tier validation) so both stay in lockstep with exactly one set.
TIERS = ("smoke", "standard", "high-assurance")

# A model from a different family than the default, so the cross-model seat does not
# share the default model's blind spots. Overridable per high-assurance panel via the
# `alt_model` argument or the `JUDGE_ALT_MODEL` environment variable.
DEFAULT_ALT_MODEL = "anthropic/claude-sonnet-5"

_ARBITER = "arbiter"


class Seat(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Role
    model: str | None = None  # None -> the evaluator's default model
    cross_model: bool = False


class Panel:
    def __init__(self, tier: str, seats: list[Seat], evaluator: Evaluator | None = None) -> None:
        if evaluator is None:
            from .openrouter import OpenRouterEvaluator

            evaluator = OpenRouterEvaluator()
        self.tier = tier
        self.seats = seats
        self.evaluator = evaluator

    def evaluate(self, subject: EvalSubject, rubric: Rubric) -> list[EvalResult]:
        results: list[EvalResult] = []
        for seat in self.seats:
            peers = tuple(c for r in results for c in r.concerns) if seat.role == _ARBITER else ()
            request = EvalRequest(
                role=seat.role,
                artifact_text=subject.artifact_text,
                contract_summary=subject.contract_summary,
                rubric=rubric,
                model=seat.model,
                cross_model=seat.cross_model,
                peer_concerns=peers,
            )
            results.append(self.evaluator.evaluate(request))
        return results

    @classmethod
    def smoke(cls, evaluator: Evaluator | None = None) -> Panel:
        return cls("smoke", [Seat(role="fault-seeker")], evaluator)

    @classmethod
    def standard(cls, evaluator: Evaluator | None = None) -> Panel:
        return cls(
            "standard",
            [Seat(role="fault-seeker"), Seat(role="conformance-checker"), Seat(role=_ARBITER)],
            evaluator,
        )

    @classmethod
    def high_assurance(
        cls, evaluator: Evaluator | None = None, alt_model: str | None = None
    ) -> Panel:
        resolved_alt = alt_model or os.environ.get("JUDGE_ALT_MODEL") or DEFAULT_ALT_MODEL
        return cls(
            "high-assurance",
            [
                Seat(role="fault-seeker"),
                Seat(role="conformance-checker"),
                Seat(role="fault-seeker", model=resolved_alt, cross_model=True),
                Seat(role=_ARBITER),
            ],
            evaluator,
        )

    @classmethod
    def for_tier(cls, tier: str, evaluator: Evaluator | None = None) -> Panel:
        factories = {
            "smoke": cls.smoke,
            "standard": cls.standard,
            "high-assurance": cls.high_assurance,
        }
        if tier not in factories:
            raise ValueError(f"unknown tier: {tier!r} (expected smoke|standard|high-assurance)")
        return factories[tier](evaluator)
