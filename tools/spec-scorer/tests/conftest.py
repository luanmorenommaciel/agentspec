"""Shared fixtures for the spec-scorer test suite.

The Scorer reuses the sibling Linter's value objects by import. There is no
published `spec_linter` package, so — exactly as the `spec-score` wrapper does at
runtime — the test session puts the sibling `tools/spec-linter` on `sys.path`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

_LINTER = Path(__file__).resolve().parents[2] / "spec-linter"
if _LINTER.is_dir() and str(_LINTER) not in sys.path:
    sys.path.insert(0, str(_LINTER))


@pytest.fixture
def valid_spec() -> dict[str, Any]:
    """A fully governance-compliant V2 spec as a fresh dict per test."""
    return {
        "id": "code-reviewer",
        "name": "Code Reviewer",
        "description": "Reviews diffs.",
        "model": "claude-opus-4",
        "tools": ["read_file"],
        "kb_domains": ["testing"],
        "maturity": "V2",
        "tier": "T2",
        "output_contract": {
            "format": "structured-report",
            "required_fields": ["summary"],
            "side_effects": {
                "files_written": False,
                "git_operations": ["none"],
                "external_apis": [],
            },
        },
        "stop_conditions": ["no diff"],
        "escalation_rules": ["escalate on security change"],
        "observability": {"confidence_scoring": True, "sources_attribution": True},
        "memory_backend": "none",
        "recall_strategy": "per-session",
        "requirements": ["lint the diff"],
        "deliverables": ["lint the diff"],
    }


@pytest.fixture
def bare_v3_spec() -> dict[str, Any]:
    """A spec that *declares* V3 but carries only V1 evidence — the maturity
    over-claim the Scorer exists to surface. Kept schema-parseable."""
    return {
        "id": "over-claimer",
        "name": "Over Claimer",
        "description": "Claims more than it shows.",
        "model": "claude-opus-4",
        "tools": ["read_file"],
        "maturity": "V3",
        "tier": "T1",
        "output_contract": {
            "format": "markdown-only",
            "required_fields": [],
            "side_effects": {
                "files_written": False,
                "git_operations": ["none"],
                "external_apis": [],
            },
        },
        "stop_conditions": ["done"],
        "escalation_rules": ["escalate on error"],
    }
