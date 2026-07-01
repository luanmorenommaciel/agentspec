"""Vocabulary sync: the closed category/severity vocab must agree across the
consensus rule table, the ``Literal`` aliases, and the hand-maintained JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import get_args

from spec_judge.consensus import _CATEGORY_RULES
from spec_judge.vocab import Category, Severity

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "evaluator_response.schema.json"


def test_category_rules_cover_exactly_the_literal_categories() -> None:
    assert set(_CATEGORY_RULES) == set(get_args(Category))


def test_schema_enums_match_the_literal_aliases() -> None:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    concern_props = schema["properties"]["concerns"]["items"]["properties"]
    assert concern_props["category"]["enum"] == sorted(get_args(Category))
    assert concern_props["severity"]["enum"] == list(get_args(Severity))
