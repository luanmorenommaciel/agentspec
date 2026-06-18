"""Unit tests for scripts/lib/frontmatter.py."""
from __future__ import annotations

from scripts.lib import frontmatter


SAMPLE_AGENT = """---
name: define-agent
description: |
  Requirements extraction and validation specialist.
  Use PROACTIVELY when capturing requirements.
tier: T2
model: sonnet
tools: [Read, Write, Edit]
kb_domains: [dbt, data-quality]
escalation_rules:
  - trigger: clarity_low
    target: brainstorm-agent
    reason: needs more exploration
  - trigger: design_ready
    target: design-agent
    reason: requirements clear
---

# Body

Some markdown.
"""


class TestParse:
    def test_parses_scalar_fields(self):
        fm = frontmatter.parse(SAMPLE_AGENT)
        assert fm.data["name"] == "define-agent"
        assert fm.data["tier"] == "T2"
        assert fm.data["model"] == "sonnet"

    def test_parses_block_description(self):
        fm = frontmatter.parse(SAMPLE_AGENT)
        description = fm.data["description"]
        assert isinstance(description, str)
        assert "Requirements extraction" in description

    def test_parses_inline_lists(self):
        fm = frontmatter.parse(SAMPLE_AGENT)
        assert fm.data["tools"] == ["Read", "Write", "Edit"]
        assert fm.data["kb_domains"] == ["dbt", "data-quality"]

    def test_extracts_escalation_targets(self):
        fm = frontmatter.parse(SAMPLE_AGENT)
        assert fm.data["escalation_rules"] == ["brainstorm-agent", "design-agent"]

    def test_returns_empty_when_no_frontmatter(self):
        fm = frontmatter.parse("# Just a heading\n")
        assert fm.data == {}
        assert fm.raw == ""

    def test_body_starts_after_frontmatter(self):
        fm = frontmatter.parse(SAMPLE_AGENT)
        assert fm.body.lstrip().startswith("# Body")


class TestRender:
    def test_render_with_scalar_fields(self):
        text = frontmatter.render(
            {"name": "x", "description": "y", "disable-model-invocation": True},
            "body\n",
        )
        assert text.startswith("---\n")
        assert "name: x" in text
        assert "disable-model-invocation: true" in text
        assert text.rstrip().endswith("body")

    def test_render_with_list(self):
        text = frontmatter.render({"tools": ["Read", "Write"]}, "body\n")
        assert "tools: [Read, Write]" in text

    def test_render_with_empty_data_returns_body(self):
        assert frontmatter.render({}, "body") == "body"
