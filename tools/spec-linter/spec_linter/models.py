"""Layer 1 (L1) — the agent spec schema, expressed as a Pydantic v2 model.

This is the single source of truth: it validates YAML specs *and* emits a JSON
Schema (`AgentSpec.model_json_schema()`), so there is no JSON-Schema-vs-Pydantic
either/or — both come from this one model.

L2 governance is deliberately *not* enforced here (see `rules.py`): an `extra="allow"`
model that passes L1 may still violate governance, and we want those reported as
structured L2 findings rather than as L1 ValidationErrors.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

GitOperation = Literal["commit", "push", "branch", "none"]
OutputFormat = Literal["structured-report", "code-file", "json", "markdown-only"]
Maturity = Literal["V1", "V2", "V3"]
Tier = Literal["T1", "T2", "T3"]
MemoryBackend = Literal["kv", "vector", "graph", "none"]
RecallStrategy = Literal["per-session", "per-user", "global"]

_KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SideEffects(BaseModel):
    files_written: bool
    git_operations: list[GitOperation]
    external_apis: list[str]


class OutputContract(BaseModel):
    format: OutputFormat
    required_fields: list[str] = Field(default_factory=list)
    side_effects: SideEffects


class Observability(BaseModel):
    confidence_scoring: bool
    sources_attribution: bool


class AgentSpec(BaseModel):
    # extra="allow" so unknown keys don't crash L1; they are surfaced as WARN
    # findings via `model_extra` (see rules.unknown_field_findings).
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: str

    model: str
    tools: list[str]
    kb_domains: list[str] = Field(default_factory=list)

    maturity: Maturity
    tier: Tier

    output_contract: OutputContract

    stop_conditions: list[str] = Field(default_factory=list)
    escalation_rules: list[str] = Field(default_factory=list)

    observability: Observability | None = None

    memory_backend: MemoryBackend | None = None
    recall_strategy: RecallStrategy | None = None

    requirements: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)

    publish: bool = False
    security_review: bool = False

    @field_validator("id")
    @classmethod
    def _id_is_kebab_case(cls, value: str) -> str:
        if not _KEBAB_CASE.match(value):
            raise ValueError("id must be kebab-case (e.g. 'my-agent-name')")
        return value
