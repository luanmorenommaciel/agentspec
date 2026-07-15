"""OpenRouterEvaluator: transport errors, the per-call budget backstop, and the
untrusted-boundary concern parsing — all offline (``_call``/``urlopen`` stubbed)."""

from __future__ import annotations

import pytest

import spec_judge.openrouter as openrouter_module
from spec_judge import ledger
from spec_judge.contracts import Rubric
from spec_judge.evaluator import EvalRequest


def _request() -> EvalRequest:
    return EvalRequest(
        role="fault-seeker", artifact_text="a", contract_summary="c", rubric=Rubric()
    )


def test_timeout_during_urlopen_raises_network_error(tmp_path, monkeypatch) -> None:
    # `TimeoutError` is an `OSError` subclass raised mid-request (after `HTTPError`/
    # `URLError` are ruled out) — ordinary API flakiness, not a blocking failure.
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    def fake_urlopen(*args, **kwargs):
        raise TimeoutError("stalled")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(openrouter_module.NetworkError):
        openrouter_module.OpenRouterEvaluator().evaluate(_request())


def test_budget_backstop_blocks_the_second_call(tmp_path, monkeypatch) -> None:
    # The library entry point (`evaluate`), not just the CLI's preflight, must refuse
    # to spend once the shared per-day budget is exhausted.
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "l.jsonl"))
    monkeypatch.setenv("JUDGE_BUDGET", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    def fake_call(self, api_key, model, request):
        return {"confidence": 0.5, "summary": "", "concerns": []}

    monkeypatch.setattr(openrouter_module.OpenRouterEvaluator, "_call", fake_call)
    evaluator = openrouter_module.OpenRouterEvaluator()
    evaluator.evaluate(_request())  # consumes the only budget slot today
    with pytest.raises(ledger.BudgetError):
        evaluator.evaluate(_request())


def test_parse_concerns_normalizes_case_and_synonyms() -> None:
    payload = {
        "confidence": 0.8,
        "concerns": [
            {
                "category": "b2",
                "severity": "critical",
                "evidence": "e",
                "expected": "x",
                "recommendation": "r",
            }
        ],
    }
    concerns = openrouter_module._parse_concerns(payload)
    assert len(concerns) == 1
    assert concerns[0].category == "B2"
    assert concerns[0].severity == "high"
