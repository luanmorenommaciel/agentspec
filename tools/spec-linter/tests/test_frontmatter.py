"""Tests for frontmatter extraction: the leading `---`-fenced YAML block of a
self-contained `.md` artifact.
"""

from __future__ import annotations

import pytest

from spec_linter.frontmatter import FrontmatterError, split_frontmatter


def test_plain_frontmatter_splits_mapping_and_body() -> None:
    text = "---\nid: code-reviewer\ntier: T2\n---\n# Code Reviewer\n\nBody text.\n"
    frontmatter, body = split_frontmatter(text)
    assert frontmatter == {"id": "code-reviewer", "tier": "T2"}
    assert body == "# Code Reviewer\n\nBody text.\n"


def test_standalone_fence_survives_an_indented_hrule_in_a_block_scalar() -> None:
    # A YAML block scalar (`description: |`) may contain a line that merely looks like
    # an hrule when indented; only a column-0 `---` is a real fence.
    text = (
        "---\n"
        "id: report-writer\n"
        "description: |\n"
        "  line one\n"
        "  ---\n"
        "  line two\n"
        "tier: T2\n"
        "---\n"
        "The real body.\n"
    )
    frontmatter, body = split_frontmatter(text)
    assert frontmatter is not None
    assert frontmatter["tier"] == "T2"
    assert frontmatter["description"] == "line one\n---\nline two\n"
    assert body == "The real body.\n"


def test_body_hrule_after_the_closing_fence_is_left_untouched() -> None:
    # A `---` hrule in the body, AFTER the real closing fence, must stay in the body —
    # it must not be mistaken for another frontmatter boundary.
    text = "---\nid: x\n---\nBefore the rule.\n---\nAfter the rule.\n"
    frontmatter, body = split_frontmatter(text)
    assert frontmatter == {"id": "x"}
    assert body == "Before the rule.\n---\nAfter the rule.\n"


def test_no_leading_fence_returns_none_mapping() -> None:
    text = "# Just a heading\n\nNo frontmatter here.\n"
    frontmatter, body = split_frontmatter(text)
    assert frontmatter is None
    assert body == text


def test_unclosed_fence_returns_none_mapping() -> None:
    # An opening fence with no closing fence is structurally absent, not malformed.
    text = "---\nid: x\nno closing fence below\n"
    frontmatter, body = split_frontmatter(text)
    assert frontmatter is None
    assert body == text


def test_malformed_yaml_inside_a_closed_fence_raises() -> None:
    text = "---\nid: [unterminated\n---\nbody\n"
    with pytest.raises(FrontmatterError):
        split_frontmatter(text)


def test_non_mapping_frontmatter_raises() -> None:
    text = "---\n- a\n- b\n---\nbody\n"
    with pytest.raises(FrontmatterError):
        split_frontmatter(text)


def test_empty_frontmatter_block_raises() -> None:
    text = "---\n---\nbody\n"
    with pytest.raises(FrontmatterError):
        split_frontmatter(text)
