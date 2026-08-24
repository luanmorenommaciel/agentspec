"""Test bootstrap: make all three packages importable without an editable install,
and keep every run offline and isolated.
"""

from __future__ import annotations

import pathlib
import sys
from collections.abc import Iterator
from typing import Any

import pytest
import yaml

# Injected at conftest-import time — before any test module imports spec_composer,
# spec_linter or spec_judge — so the suite runs without an editable install.
_TESTS = pathlib.Path(__file__).resolve().parent  # tools/spec-composer/tests
_PKG_ROOT = _TESTS.parent  # tools/spec-composer  (contains spec_composer/)
_LINTER = _TESTS.parents[1] / "spec-linter"  # tools/spec-linter (contains spec_linter/)
_JUDGE = _TESTS.parents[1] / "spec-judge"  # tools/spec-judge  (contains spec_judge/)
for _path in (_PKG_ROOT, _LINTER, _JUDGE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

TOOL_ROOT = _PKG_ROOT
PIPELINES = _PKG_ROOT / "pipelines"
EXAMPLES = _PKG_ROOT / "examples"
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


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> Iterator[None]:
    """Structurally prevent an accidental paid call and any shared state: no
    provider credential, a per-test run root, a per-test judge ledger, and a
    per-test workspace so the archive never escapes the temporary directory."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("COMPOSER_RUN_ROOT", str(tmp_path / "run-state"))
    monkeypatch.setenv("JUDGE_LEDGER", str(tmp_path / "judge-ledger.jsonl"))
    (tmp_path / ".claude").mkdir(exist_ok=True)
    monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture
def shipped_document() -> dict[str, Any]:
    """The shipped pipeline contract as a fresh mapping per test."""
    return yaml.safe_load(SHIPPED_PIPELINE.read_text(encoding="utf-8"))


@pytest.fixture
def spec_text() -> str:
    return SPEC_TEXT


@pytest.fixture
def agent_text() -> str:
    return AGENT_TEXT


@pytest.fixture
def rejected_agent_text() -> str:
    return REJECTED_AGENT_TEXT


@pytest.fixture
def written_spec(tmp_path: pathlib.Path) -> pathlib.Path:
    """A creation spec on disk that passes the creation-spec contract."""
    path = tmp_path / "specs" / "code-reviewer.spec.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SPEC_TEXT, encoding="utf-8")
    return path


@pytest.fixture
def target(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / ".claude" / "agents" / "dev" / "code-reviewer.md"


def judge_less_document() -> dict[str, Any]:
    """The shipped lifecycle with the judge stage removed — a pipeline may omit
    it, and every offline end-to-end test uses this form."""
    document = yaml.safe_load(SHIPPED_PIPELINE.read_text(encoding="utf-8"))
    document["stages"] = [stage for stage in document["stages"] if stage["kind"] != "judge"]
    return document
