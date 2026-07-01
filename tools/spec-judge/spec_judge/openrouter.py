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

from . import ledger, prompts
from .evaluator import Concern, EvalRequest, EvalResult

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"
_VALID_CATEGORIES = {"B1", "B2", "B3", "B4"}
_VALID_SEVERITIES = {"high", "medium", "low"}


class ConfigError(RuntimeError):
    """Missing/invalid configuration (e.g. no API key). The CLI maps this to exit 2."""


class NetworkError(RuntimeError):
    """Transport/API failure or an unparseable response. The CLI maps this to exit 4."""


def _parse_concerns(payload: dict) -> tuple[Concern, ...]:
    concerns: list[Concern] = []
    for raw in payload.get("concerns", []) or []:
        if not isinstance(raw, dict):
            continue
        category = str(raw.get("category", "")).strip()
        severity = str(raw.get("severity", "")).strip().lower()
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


def _coerce_confidence(payload: dict) -> float:
    try:
        value = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, value))


def _extract_json(raw: str) -> dict:
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

    def _call(self, api_key: str, model: str, request: EvalRequest) -> dict:
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
        return _extract_json(raw)
