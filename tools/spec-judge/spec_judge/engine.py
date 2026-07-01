"""The engine — one entry point, pure orchestration.

``judge(artifact, contract, panel) -> Verdict`` mirrors the Linter's
``lint(artifact, contract) -> Verdict`` and returns the **same** ``Verdict`` type,
so a consumer handles both the structural and behavioral gates with one code path.

The engine has zero model vocabulary and zero I/O of its own: the contract parses,
the panel runs the model calls, consensus folds results into a verdict. An
unparseable artifact mirrors the Linter's engine — a single ``FAIL`` finding — but
in practice the CLI screens missing/empty input as an operational error (exit 2)
before reaching here, since the Judger only runs on a structural PASS.
"""

from __future__ import annotations

from spec_linter import Finding, Level, Verdict

from .consensus import consensus
from .panel import Panel
from .protocol import BehavioralContract


def judge(artifact: object, contract: BehavioralContract, panel: Panel | None = None) -> Verdict:
    try:
        subject = contract.parse(artifact)
    except Exception as exc:  # noqa: BLE001 — the contract decides what "unparseable" means
        return Verdict.from_findings(
            [Finding(level=Level.FAIL, rule=f"{contract.name}.unparseable", message=str(exc))]
        )
    panel = panel or Panel.standard()
    results = panel.evaluate(subject, contract.rubric())
    return consensus(results, tier=panel.tier)
