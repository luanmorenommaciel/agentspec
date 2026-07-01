"""The two seams the Linter's ``Contract`` lacks.

The Linter's ``Contract`` is ``parse + check`` where ``check`` is pure policy (no
I/O). Behavioral evaluation needs a model call, which must NOT live in the contract.
So the responsibility is split:

- ``BehavioralContract`` — policy: normalize the artifact + declare what to probe.
- ``Evaluator`` — mechanism: the model call, injected so tests use a fake.

Both are structural (``Protocol``): concrete classes satisfy them by shape, not by
inheritance, exactly like the Linter's ``Contract``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .contracts import EvalSubject, Rubric
from .evaluator import EvalRequest, EvalResult


@runtime_checkable
class BehavioralContract(Protocol):
    name: str

    def parse(self, artifact: object) -> EvalSubject:
        """Normalize the artifact and bind the source spec, or raise if unparseable."""
        ...

    def rubric(self) -> Rubric:
        """The categories to probe + the severity policy."""
        ...


@runtime_checkable
class Evaluator(Protocol):
    name: str

    def evaluate(self, request: EvalRequest) -> EvalResult:
        """Judge one request (the model call). Reports concerns + confidence, not a verdict."""
        ...
