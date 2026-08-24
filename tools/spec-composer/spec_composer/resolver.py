"""Contract resolution — a stage's contract NAME bound to a contract object.

There is no registry and no plugin discovery: a resolver is a per-run map that
the caller injects, exactly as the Judger injects an evaluator. `DefaultResolver`
carries the bindings the shipped pipeline needs; a consumer with another artifact
type passes its own map instead of editing this module.
"""

from __future__ import annotations

from spec_linter import AgentSpecContract, Contract, CreationSpecContract


class UnresolvedContract(LookupError):
    """A pipeline names a contract that has no binding in this installation.

    A configuration defect, not a transient failure: re-running cannot clear it.
    """


class DefaultResolver:
    name = "default"

    def __init__(self, bindings: dict[str, Contract] | None = None) -> None:
        self._bindings: dict[str, Contract] = (
            dict(bindings)
            if bindings is not None
            else {
                "creation-spec": CreationSpecContract(),
                "agent-spec": AgentSpecContract(),
            }
        )
        self.known = frozenset(self._bindings)

    def resolve(self, contract_name: str) -> Contract:
        try:
            return self._bindings[contract_name]
        except KeyError as exc:
            known = ", ".join(sorted(self.known)) or "(none)"
            raise UnresolvedContract(
                f"no contract is bound to {contract_name!r} here; bound names: {known}"
            ) from exc
