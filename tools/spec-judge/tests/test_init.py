"""``spec_judge/__init__.py``: the PEP 562 lazy export of ``judge`` and the sibling
``Verdict``/``Finding``/``Level`` types — the two names that need ``spec_linter``."""

from __future__ import annotations

import pytest

import spec_judge
import spec_judge.engine


def test_judge_is_the_same_object_as_engine_judge() -> None:
    assert spec_judge.judge is spec_judge.engine.judge


def test_lazily_exports_the_sibling_verdict_types() -> None:
    from spec_linter import Finding, Level, Verdict

    assert spec_judge.Verdict is Verdict
    assert spec_judge.Finding is Finding
    assert spec_judge.Level is Level


def test_unknown_attribute_raises_attribute_error() -> None:
    with pytest.raises(AttributeError):
        getattr(spec_judge, "nonexistent_name")
