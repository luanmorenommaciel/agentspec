"""Fixtures shared by the suite as plain values: paths, artifact bodies, and the
pipeline documents the offline tests run. Kept out of `conftest.py` so a test
module imports what it uses by name rather than reaching into the plugin.
"""

from __future__ import annotations

import pathlib
from typing import Any

import yaml

_TESTS = pathlib.Path(__file__).resolve().parent

TOOL_ROOT = _TESTS.parent
PIPELINES = TOOL_ROOT / "pipelines"
EXAMPLES = TOOL_ROOT / "examples"
SHIPPED_PIPELINE = PIPELINES / "agent-creation.yaml"

SPEC_TEXT = """---
name: code-reviewer
intent: Review Python diffs against the house standards and report structured findings
overlap_check: 0.21
trigger_count: 4
tier: T2
---

# code-reviewer

The reviewer reads a diff and reports findings against the house standards.
"""

AGENT_TEXT = """---
id: code-reviewer
name: Code Reviewer
description: Reviews Python diffs against house standards and emits a structured report.
model: claude-opus-4
tools:
  - read_file
kb_domains:
  - python-standards
maturity: V2
tier: T2
output_contract:
  format: structured-report
  required_fields:
    - summary
  side_effects:
    files_written: false
    git_operations:
      - none
    external_apis: []
stop_conditions:
  - no diff provided
escalation_rules:
  - escalate to human on security-sensitive change
observability:
  confidence_scoring: true
  sources_attribution: true
memory_backend: none
recall_strategy: per-session
requirements:
  - lint the diff
deliverables:
  - lint the diff
publish: false
security_review: false
---

# Code Reviewer

Reads a Python diff and reports findings against the house standards.
"""

# Structurally valid frontmatter that FAILS the agent-spec governance rules:
# no stop conditions and no escalation rules (L2), so Gate B rejects it.
REJECTED_AGENT_TEXT = AGENT_TEXT.replace(
    "stop_conditions:\n  - no diff provided\n", "stop_conditions: []\n"
).replace(
    "escalation_rules:\n  - escalate to human on security-sensitive change\n",
    "escalation_rules: []\n",
)

# Two producing stages feeding one emit — the shape that proves staging paths are
# scoped per stage, not only per attempt.
TWO_PRODUCER_PIPELINE: dict[str, Any] = {
    "pipeline": "two-producers",
    "version": 1,
    "max_attempts": 3,
    "archive": ".claude/sdd/archive/specs/{name}/",
    "stages": [
        {"id": "create-spec", "kind": "create", "output_contract": "creation-spec"},
        {"id": "gate-a", "kind": "lint", "input_contract": "creation-spec"},
        {
            "id": "draft-agent",
            "kind": "generate",
            "input_contract": "creation-spec",
            "output_contract": "agent-spec",
        },
        {"id": "gate-draft", "kind": "lint", "input_contract": "agent-spec"},
        {
            "id": "refine-agent",
            "kind": "generate",
            "input_contract": "creation-spec",
            "output_contract": "agent-spec",
        },
        {"id": "gate-refined", "kind": "lint", "input_contract": "agent-spec"},
        {"id": "emit-agent", "kind": "emit"},
    ],
}


def shipped_pipeline_document() -> dict[str, Any]:
    """The shipped pipeline contract as a fresh mapping per call."""
    return yaml.safe_load(SHIPPED_PIPELINE.read_text(encoding="utf-8"))


def judge_less_document() -> dict[str, Any]:
    """The shipped lifecycle with the judge stage removed — a pipeline may omit
    it, and every offline end-to-end test uses this form."""
    document = shipped_pipeline_document()
    document["stages"] = [stage for stage in document["stages"] if stage["kind"] != "judge"]
    return document
