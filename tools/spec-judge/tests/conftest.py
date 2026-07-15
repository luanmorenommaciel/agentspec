"""Test bootstrap: make both packages importable without an editable install, and
supply shared fixtures.

The Judger reuses the Linter's value objects by import. In a dev checkout there is
no venv on PYTHONPATH, so we inject the sibling ``spec-linter`` dir (and this
package's own root) onto ``sys.path`` before any test imports run.
"""

from __future__ import annotations

import pathlib
import sys
from collections.abc import Iterator
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


@pytest.fixture(autouse=True)
def _no_api_key(request, monkeypatch) -> Iterator[None]:
    """Structurally prevent an accidental paid call: strip ``OPENROUTER_API_KEY`` from
    the environment for every test, except one explicitly marked ``live`` (which needs
    a real key to run at all — see the ``live`` marker registered in ``pyproject.toml``).
    A test that stubs the evaluator but still wants a key present sets it itself, after
    this fixture has already run.
    """
    if "live" in request.keywords:
        yield
        return
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    yield


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
        "stop_conditions": ["stop when the diff exceeds 5000 lines"],
        "observability": {"confidence_scoring": True, "sources_attribution": True},
    }
