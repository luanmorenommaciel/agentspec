"""OpenRouterEvaluator — the real model call.

A thin OpenRouter client: build the role prompt, POST, parse concerns + confidence,
write the shared ledger, and raise typed errors the CLI maps to exit codes. The API
key is read at call time (never at construction), so constructing the evaluator — and
therefore the default panel — is free and offline, which keeps every unit test off the
network.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, get_args

from . import ledger, prompts
from .evaluator import Concern, EvalRequest, EvalResult
from .vocab import Category, Severity

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"
_VALID_CATEGORIES = set(get_args(Category))
_VALID_SEVERITIES = set(get_args(Severity))
_SEVERITY_SYNONYMS = {"critical": "high"}


class ConfigError(RuntimeError):
    """Missing/invalid configuration (e.g. no API key). The CLI maps this to exit 2."""


class NetworkError(RuntimeError):
    """Transport/API failure or an unparseable response. The CLI maps this to exit 4."""


def _parse_concerns(payload: dict[str, Any]) -> tuple[Concern, ...]:
    """Filter+normalize the model's raw ``concerns`` at this untrusted boundary.

    Category/severity are case- and synonym-normalized before validation
    (``"b2"`` -> ``"B2"``, ``"critical"`` -> ``"high"``). A concern that still
    doesn't name a valid category/severity is dropped, not raised on — the
    full untouched payload stays available in ``EvalResult.raw`` for debugging.
    """
    concerns: list[Concern] = []
    for raw in payload.get("concerns", []) or []:
        if not isinstance(raw, dict):
            continue
        category = str(raw.get("category", "")).strip().upper()
        severity = str(raw.get("severity", "")).strip().lower()
        severity = _SEVERITY_SYNONYMS.get(severity, severity)
        if category not in _VALID_CATEGORIES or severity not in _VALID_SEVERITIES:
            continue
        concerns.append(
            Concern(
                category=category,
                severity=severity,
                evidence=str(raw.get("evidence", "")),
                expected=str(raw.get("expected", "")),
                recommendation=str(raw.get("recommendation", "")),
            )
        )
    return tuple(concerns)


def _coerce_confidence(payload: dict[str, Any]) -> float:
    try:
        value = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, value))


def _extract_json(raw: str) -> dict[str, Any]:
    try:
        content = json.loads(raw)["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise NetworkError(f"unexpected OpenRouter response: {raw[:300]}") from exc
    content = re.sub(r"^```(?:json)?\s*\n?", "", content.strip())
    content = re.sub(r"\n?```\s*$", "", content)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise NetworkError(f"model did not return JSON: {content[:300]}") from exc
    if not isinstance(parsed, dict):
        raise NetworkError("model response JSON was not an object")
    return parsed


class OpenRouterEvaluator:
    name = "openrouter"

    def __init__(self, *, default_model: str | None = None, timeout: int = 60) -> None:
        self._default_model = default_model
        self._timeout = timeout

    def _resolve_model(self, request: EvalRequest) -> str:
        if request.model:
            return request.model
        return self._default_model or os.environ.get("JUDGE_MODEL", DEFAULT_MODEL)

    def evaluate(self, request: EvalRequest) -> EvalResult:
        if ledger.today_count() >= ledger.budget():
            raise ledger.BudgetError(
                f"per-day evaluation budget exhausted ({ledger.budget()} calls)"
            )
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ConfigError("OPENROUTER_API_KEY not set")
        model = self._resolve_model(request)
        payload = self._call(api_key, model, request)
        concerns = _parse_concerns(payload)
        ledger.append(model=model, role=request.role, verdict="concerns" if concerns else "clean")
        return EvalResult(
            role=request.role,
            model=model,
            cross_model=request.cross_model,
            confidence=_coerce_confidence(payload),
            summary=str(payload.get("summary", "")),
            concerns=concerns,
            raw=payload,
        )

    def _call(self, api_key: str, model: str, request: EvalRequest) -> dict[str, Any]:
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": prompts.system_prompt(request.role, request.rubric)},
                {
                    "role": "user",
                    "content": prompts.user_prompt(
                        request.contract_summary, request.artifact_text, request.peer_concerns
                    ),
                },
            ],
            "temperature": 0.1,
            "max_tokens": 1500,
        }
        http_request = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-Title": "AgentSpec Judger",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self._timeout) as response:
                raw = response.read().decode()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode() if exc.fp else ""
            raise NetworkError(f"OpenRouter HTTP {exc.code}: {detail[:300]}") from exc
        except urllib.error.URLError as exc:
            raise NetworkError(f"network error: {exc.reason}") from exc
        except OSError as exc:
            # Supertype of TimeoutError and other socket-level failures that occur
            # mid-response (after urlopen succeeds), e.g. a stall during response.read().
            raise NetworkError(f"network error: {exc}") from exc
        return _extract_json(raw)
