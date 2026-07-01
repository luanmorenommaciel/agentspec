"""Test bootstrap: make both packages importable without an editable install, and
supply shared fixtures.

The Judger reuses the Linter's value objects by import. In a dev checkout there is
no venv on PYTHONPATH, so we inject the sibling ``spec-linter`` dir (and this
package's own root) onto ``sys.path`` before any test imports run.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Any

import pytest

# Inject both package roots at conftest import time — before any test module imports
# spec_judge / spec_linter — so the suite runs without an editable install.
_TESTS = pathlib.Path(__file__).resolve().parent  # tools/spec-judge/tests
_PKG_ROOT = _TESTS.parent  # tools/spec-judge (contains spec_judge/)
_LINTER = _TESTS.parents[1] / "spec-linter"  # tools/spec-linter (contains spec_linter/)
for _path in (_PKG_ROOT, _LINTER):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


@pytest.fixture
def source_spec() -> dict[str, Any]:
    """A minimal source spec: an artifact generated from it must honor this contract."""
    return {
        "id": "code-reviewer",
        "description": "Reviews Python diffs against house standards.",
        "output_contract": {
            "format": "structured-report",
            "required_fields": ["summary", "findings"],
            "side_effects": {
                "files_written": False,
                "git_operations": ["none"],
                "external_apis": [],
            },
        },
        "requirements": ["lint the diff"],
        "deliverables": ["lint the diff"],
    }
