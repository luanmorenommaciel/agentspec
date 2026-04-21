"""Unit tests for scripts/generate-agent-router.py pure functions.

Targets the frontmatter parser, one-liner extractor, and the AgentSpec
dataclass invariant. Discovery of real agents is exercised by the
``--check`` integration run in CI; these tests focus on regression bait.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_generator():
    """Load scripts/generate-agent-router.py by path.

    The filename has a dash so we cannot import-by-package. We register the
    loaded module in ``sys.modules`` before execution so the dataclass
    decorator can resolve forward references (required on Python 3.11+).
    """
    import sys
    spec_path = Path(__file__).resolve().parent.parent / "scripts" / "generate-agent-router.py"
    spec = importlib.util.spec_from_file_location("generator_mod", spec_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["generator_mod"] = module   # dataclass forward-reference fix
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


# ── parse_frontmatter ────────────────────────────────────────────────────────

class TestParseFrontmatter:
    def test_parses_simple_fields(self, gen):
        text = """---
name: my-agent
tier: T2
model: sonnet
kb_domains: [a, b, c]
---

# body
"""
        fm = gen.parse_frontmatter(text)
        assert fm["name"] == "my-agent"
        assert fm["tier"] == "T2"
        assert fm["model"] == "sonnet"
        assert fm["kb_domains"] == ["a", "b", "c"]

    def test_empty_kb_domains(self, gen):
        text = """---
name: lean-agent
kb_domains: []
---
body
"""
        fm = gen.parse_frontmatter(text)
        assert fm["kb_domains"] == []

    def test_no_frontmatter_returns_empty(self, gen):
        assert gen.parse_frontmatter("no delimiters here") == {}

    def test_block_scalar_description(self, gen):
        text = """---
name: block-desc
description: |
  One-line purpose.
  Use PROACTIVELY when things happen.
---
body
"""
        fm = gen.parse_frontmatter(text)
        assert "description" in fm
        assert "One-line purpose" in str(fm["description"])

    def test_extracts_escalation_targets(self, gen):
        text = """---
name: escalating-agent
escalation_rules:
  - trigger: "foo"
    target: "target-agent-a"
    reason: "because"
  - trigger: "bar"
    target: target-agent-b
    reason: "also"
---
body
"""
        fm = gen.parse_frontmatter(text)
        assert fm.get("escalates_to") == ["target-agent-a", "target-agent-b"]


# ── extract_one_liner ────────────────────────────────────────────────────────

class TestExtractOneLiner:
    def test_first_meaningful_line_wins(self, gen):
        desc = """
        Data modeling specialist for dimensional modeling.
        Use PROACTIVELY when designing schemas.

        <example>
        ...
        </example>
        """
        line = gen.extract_one_liner(desc)
        assert "specialist" in line.lower()

    def test_stops_at_example_blocks(self, gen):
        """When the first meaningful line starts with <example>, the extractor
        falls back to the very first stripped line — this is the current
        conservative behavior, we're pinning it against regression."""
        desc = """
        Real one-liner here.
        <example>
        This should not be the one-liner.
        </example>
        """
        line = gen.extract_one_liner(desc)
        assert line == "Real one-liner here."

    def test_empty_input(self, gen):
        assert gen.extract_one_liner("") == ""


# ── AgentSpec invariants ─────────────────────────────────────────────────────

class TestAgentSpec:
    def test_is_frozen(self, gen):
        spec = gen.AgentSpec(
            name="x", category="dev", path="p", tier="T1",
            model="sonnet", description="desc",
        )
        with pytest.raises(Exception):  # FrozenInstanceError on 3.11+
            spec.name = "y"  # type: ignore[misc]

    def test_defaults_empty_tuples(self, gen):
        spec = gen.AgentSpec(
            name="x", category="dev", path="p", tier="T1",
            model="sonnet", description="desc",
        )
        assert spec.kb_domains == ()
        assert spec.escalates_to == ()

    def test_accepts_tuples(self, gen):
        spec = gen.AgentSpec(
            name="x", category="dev", path="p", tier="T1",
            model="sonnet", description="desc",
            kb_domains=("a", "b"),
            escalates_to=("c",),
        )
        assert spec.kb_domains == ("a", "b")


# ── content_hash_for: determinism ────────────────────────────────────────────

class TestContentHash:
    def test_identical_inputs_hash_identically(self, gen):
        spec = gen.AgentSpec(
            name="a", category="dev", path="p", tier="T1",
            model="sonnet", description="d",
        )
        h1 = gen.content_hash_for([spec])
        h2 = gen.content_hash_for([spec])
        assert h1 == h2

    def test_order_independent(self, gen):
        """Generator sorts specs by name internally so hash must be stable
        regardless of input order."""
        spec_a = gen.AgentSpec(name="a", category="dev", path="p", tier="T1",
                               model="sonnet", description="d")
        spec_b = gen.AgentSpec(name="b", category="dev", path="p", tier="T1",
                               model="sonnet", description="d")
        assert gen.content_hash_for([spec_a, spec_b]) == gen.content_hash_for([spec_b, spec_a])
