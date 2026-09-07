"""Test bootstrap: make both packages importable without an editable install, and
supply shared fixtures.

The Scorer imports its own `spec_scorer` package and reuses the sibling Linter's
value objects (`spec_linter`). In a dev checkout — or under an IDE that discovers
from the workspace root rather than this directory — neither is on `sys.path`, so
we inject this package's own root AND the sibling `spec-linter` dir at conftest
import time, before any test module imports run. Mirrors spec-judge's conftest.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

_TESTS = Path(__file__).resolve().parent  # tools/spec-scorer/tests
_PKG_ROOT = _TESTS.parent  # tools/spec-scorer (contains spec_scorer/)
_LINTER = _TESTS.parents[1] / "spec-linter"  # tools/spec-linter (contains spec_linter/)
for _path in (_PKG_ROOT, _LINTER):
    if _path.is_dir() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


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
