"""The seams the conductor receives — every non-deterministic stage is injected.

`ContractResolver` binds a stage's contract NAME to a Linter contract object;
`Generator` produces the artifact a model stage is responsible for, and serves
BOTH producing kinds (`create` and `generate`) so the host loop is one shape.
Both are structural: a concrete class satisfies them by shape, exactly like the
Linter's `Contract` and the Judger's `Evaluator`. The behavioral seam is the
Judger's own `Evaluator`, referenced only under TYPE_CHECKING so that sibling
stays optional.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .models import GenerationOutcome, GenerationRequest

if TYPE_CHECKING:
    from spec_linter import Contract


@runtime_checkable
class ContractResolver(Protocol):
    name: str
    known: frozenset[str]

    def resolve(self, contract_name: str) -> Contract:
        """Return the contract bound to `contract_name`, or raise
        `UnresolvedContract` when the name has no binding here."""
        ...


@runtime_checkable
class Generator(Protocol):
    name: str

    def generate(self, request: GenerationRequest) -> GenerationOutcome:
        """Produce the stage's output at `request.output_path` for this attempt,
        or report that it is not yet available so the conductor can hand off."""
        ...
