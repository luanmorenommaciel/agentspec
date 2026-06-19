"""Validation engine — pure mechanism.

`lint(artifact, contract)` is the single entry point: parse the artifact via
the contract, run the contract's checks, assemble a Verdict. The engine has
ZERO usage vocabulary and ZERO knowledge of what the artifact or contract mean.
"""

from __future__ import annotations

from typing import Any

from .protocol import Contract
from .verdict import Finding, Level, Verdict


def lint(artifact: Any, contract: Contract) -> Verdict:
    try:
        parsed = contract.parse(artifact)
    except Exception as exc:  # contract decides what 'unparseable' means
        return Verdict.from_findings(
            [Finding(level=Level.FAIL, rule=f"{contract.name}.unparseable", message=str(exc))]
        )
    return Verdict.from_findings(contract.check(parsed))
