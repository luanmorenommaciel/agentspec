"""Behavioral contract — the source spec becomes the rule for its own artifact.

Policy only. A behavioral contract declares WHAT the artifact must honor (the
rendered ``output_contract`` + intent) and WHICH categories to probe (the rubric).
It performs no model I/O: the ``Evaluator`` does the model call, the engine
orchestrates. This mirrors the Linter's ``derived_from_instance`` binding, where a
spec's own declaration becomes the rule for the artifact produced from it.
"""

from __future__ import annotations

import json
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

_DEFAULT_SEVERITY_GUIDANCE = (
    'Reserve "high" severity for a defect that means the artifact does NOT honor a '
    'declared capability or the stated intent. Use "medium"/"low" for weaknesses that '
    "still leave the contract honored."
)

_CATEGORY_GUIDANCE = """\
B1 vagueness                — an instruction too vague to act on reliably.
B2 capability-not-delivered — a capability the contract declares that the body never
                              delivers (e.g. declares a required field, or a write
                              side-effect, that the body never produces).
B3 internal-contradiction   — instructions that conflict with each other or the contract.
B4 intent-drift             — coherent, but doing something other than what the source
                              spec asked for.
Judge ONLY against the provided contract + intent. Do not invent requirements."""


class Rubric(BaseModel):
    """What to probe + the severity policy. Frozen value object."""

    model_config = ConfigDict(frozen=True)

    categories: tuple[str, ...] = ("B1", "B2", "B3", "B4")
    severity_guidance: str = _DEFAULT_SEVERITY_GUIDANCE
    category_guidance: str = _CATEGORY_GUIDANCE


class EvalSubject(BaseModel):
    """The normalized thing an evaluator judges: artifact text against a contract."""

    model_config = ConfigDict(frozen=True)

    artifact_text: str
    contract_summary: str
    source_spec_id: str


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if value in (None, ""):
        return []
    return [str(value)]


def _render_contract_summary(spec: dict[str, Any]) -> str:
    """Project the source spec into the 'what it promised' string evaluators judge against."""
    lines: list[str] = [f"id: {spec.get('id', '?')}"]
    if spec.get("description"):
        lines.append(f"description (intent): {spec['description']}")
    output_contract = spec.get("output_contract")
    if isinstance(output_contract, dict):
        if output_contract.get("format"):
            lines.append(f"output_contract.format: {output_contract['format']}")
        required = _as_list(output_contract.get("required_fields"))
        if required:
            lines.append(f"output_contract.required_fields: {', '.join(required)}")
        side_effects = output_contract.get("side_effects")
        if isinstance(side_effects, dict):
            lines.append(
                "output_contract.side_effects: "
                f"files_written={side_effects.get('files_written')}, "
                f"git_operations={_as_list(side_effects.get('git_operations'))}, "
                f"external_apis={_as_list(side_effects.get('external_apis'))}"
            )
    requirements = _as_list(spec.get("requirements"))
    if requirements:
        lines.append("requirements (intent):\n  - " + "\n  - ".join(requirements))
    deliverables = _as_list(spec.get("deliverables"))
    if deliverables:
        lines.append("deliverables (intent):\n  - " + "\n  - ".join(deliverables))
    return "\n".join(lines)


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Split a self-contained ``---``-fenced document into (frontmatter mapping, body).

    Supports the self-contained artifact model where the spec lives in the artifact's
    own YAML frontmatter. Returns ``(None, original text)`` when there is no YAML-mapping
    frontmatter — e.g. a plain artifact whose source spec is supplied separately.
    """
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return None, text
    parts = stripped.split("---", 2)
    if len(parts) < 3:
        return None, text
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None, text
    if not isinstance(data, dict):
        return None, text
    return data, parts[2].lstrip("\n")


def _render_artifact(artifact: object) -> str:
    if isinstance(artifact, str):
        return artifact
    return json.dumps(artifact, indent=2, sort_keys=True, ensure_ascii=False, default=str)


class SpecConformanceContract:
    """Satisfies the ``BehavioralContract`` protocol. The source spec IS the contract:
    its ``output_contract`` + intent are what the produced artifact must honor."""

    def __init__(self, source_spec: dict[str, Any]) -> None:
        self._spec = source_spec
        self.name = f"spec-conformance:{source_spec.get('id', '?')}"

    def parse(self, artifact: object) -> EvalSubject:
        text = _render_artifact(artifact)
        if not text.strip():
            raise ValueError("empty artifact")
        return EvalSubject(
            artifact_text=text,
            contract_summary=_render_contract_summary(self._spec),
            source_spec_id=str(self._spec.get("id", "?")),
        )

    def rubric(self) -> Rubric:
        return Rubric()
