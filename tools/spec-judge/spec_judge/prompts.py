"""Role system prompts + the response schema, re-scoped to contract conformance.

Every role emits the SAME JSON — concerns + confidence, and deliberately NO verdict:
the engine computes the verdict (``consensus.py``), so verdict policy lives in one
place. Prompts are lean by design — they let the model reason rather than over-
constraining it (a thin layer over the primitive).
"""

from __future__ import annotations

import json

from .contracts import Rubric
from .evaluator import Concern

_RESPONSE_SCHEMA = """\
Return ONLY this JSON object — no prose, no markdown fences:
{
  "confidence": 0.0,
  "summary": "one sentence",
  "concerns": [
    {"category": "B1|B2|B3|B4", "severity": "high|medium|low",
     "evidence": "quoted text from the artifact",
     "expected": "what the contract required",
     "recommendation": "the concrete fix"}
  ]
}
If the artifact honors its contract, return an empty concerns array."""

_FAULT_SEEKER = (
    "You are an ADVERSARIAL conformance reviewer. Assume this artifact FAILS to honor "
    "its contract and find where. Your value is in the defects you surface, not in "
    "approval. Probe every category below against the contract + intent. Cite exact "
    "quoted text as evidence."
)

_CONFORMANCE_CHECKER = (
    "You are a BALANCED conformance reviewer. For each capability the contract declares "
    "(output format, required fields, side-effects) and each stated intent, verify the "
    "body delivers it. Report concerns even-handedly — neither hunting nor excusing. "
    "Cite quoted evidence."
)

_ARBITER = (
    "You are the ARBITER. You are given peer reviewers' concerns plus the artifact and "
    "its contract. Adjudicate each peer concern: uphold it (restate it) only if the "
    "artifact text supports it, or drop it if unsupported. Add any conformance defect "
    'they missed. Be decisive: "high" severity means a confident, contract-grounded '
    "blocker."
)

_ROLE_INTROS = {
    "fault-seeker": _FAULT_SEEKER,
    "conformance-checker": _CONFORMANCE_CHECKER,
    "arbiter": _ARBITER,
}


def system_prompt(role: str, rubric: Rubric) -> str:
    intro = _ROLE_INTROS.get(role, _CONFORMANCE_CHECKER)
    return (
        f"{intro}\n\n"
        f"Categories to probe:\n{rubric.category_guidance}\n\n"
        f"Severity guidance:\n{rubric.severity_guidance}\n\n"
        f"{_RESPONSE_SCHEMA}"
    )


def user_prompt(
    contract_summary: str, artifact_text: str, peer_concerns: tuple[Concern, ...] = ()
) -> str:
    parts = [
        "CONTRACT (what the artifact must honor):",
        contract_summary,
        "",
        "ARTIFACT (the produced body to judge):",
        "-----",
        artifact_text,
        "-----",
    ]
    if peer_concerns:
        peers = [
            {
                "category": c.category,
                "severity": c.severity,
                "evidence": c.evidence,
                "expected": c.expected,
                "recommendation": c.recommendation,
            }
            for c in peer_concerns
        ]
        parts += [
            "",
            "PEER CONCERNS to adjudicate:",
            json.dumps(peers, indent=2, ensure_ascii=False),
        ]
    return "\n".join(parts)
