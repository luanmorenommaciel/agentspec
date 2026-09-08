"""Test bootstrap: make all three packages importable without an editable install,
and keep every run offline and isolated. Shared values live in `_helpers.py`.
"""

from __future__ import annotations

import pathlib
import sys
from collections.abc import Iterator
from typing import Any

import pytest

# Injected at conftest-import time — before any test module imports spec_composer,
# spec_linter or spec_judge — so the suite runs without an editable install.
_TESTS = pathlib.Path(__file__).resolve().parent  # tools/spec-composer/tests
_PKG_ROOT = _TESTS.parent  # tools/spec-composer  (contains spec_composer/)
_LINTER = _TESTS.parents[1] / "spec-linter"  # tools/spec-linter (contains spec_linter/)
_JUDGE = _TESTS.parents[1] / "spec-judge"  # tools/spec-judge  (contains spec_judge/)
for _path in (_TESTS, _PKG_ROOT, _LINTER, _JUDGE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from _helpers import (
    AGENT_TEXT,
    REJECTED_AGENT_TEXT,
    SPEC_TEXT,
    shipped_pipeline_document,
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
    return shipped_pipeline_document()


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
