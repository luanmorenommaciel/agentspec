"""One real OpenRouter call — skipped unless OPENROUTER_API_KEY is set.

Every other test in this suite is offline and deterministic (FakeEvaluator). This is
the only test that touches the network, and it is opt-in and bounded by the shared
budget ledger.
"""

from __future__ import annotations

import os

import pytest

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.environ.get("OPENROUTER_API_KEY"), reason="no OPENROUTER_API_KEY set"
    ),
]


def test_one_real_evaluation(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "ledger.jsonl"))
    from spec_judge.contracts import Rubric
    from spec_judge.evaluator import EvalRequest
    from spec_judge.openrouter import OpenRouterEvaluator

    request = EvalRequest(
        role="fault-seeker",
        artifact_text="This agent claims to review diffs but its body only greets the user.",
        contract_summary="output_contract.required_fields: summary, findings",
        rubric=Rubric(),
    )
    result = OpenRouterEvaluator().evaluate(request)
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.concerns, tuple)
