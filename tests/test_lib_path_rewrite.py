"""Unit tests for scripts/lib/path_rewrite.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib import path_rewrite, platforms


@pytest.fixture
def claude_profile():
    return platforms.get_profile(platforms.CLAUDE)


@pytest.fixture
def cursor_profile():
    return platforms.get_profile(platforms.CURSOR)


class TestRewriteText:
    def test_rewrites_plugin_dirs_to_token(self, claude_profile):
        text = "See .claude/agents/workflow/define-agent.md for details."
        result = path_rewrite.rewrite_text(text, claude_profile)
        assert ".claude/agents/" not in result
        assert "${CLAUDE_PLUGIN_ROOT}/agents/" in result

    def test_uses_cursor_token_for_cursor_profile(self, cursor_profile):
        text = "Skill at .claude/skills/agent-router/SKILL.md"
        result = path_rewrite.rewrite_text(text, cursor_profile)
        assert "${PLUGIN_ROOT}/skills/agent-router/SKILL.md" in result

    def test_preserves_workspace_paths(self, claude_profile):
        text = "Outputs go to .claude/sdd/features/MY_FEATURE.md"
        result = path_rewrite.rewrite_text(text, claude_profile)
        assert ".claude/sdd/features" in result

    def test_handles_sdd_templates(self, claude_profile):
        text = "Template at .claude/sdd/templates/DEFINE_TEMPLATE.md"
        result = path_rewrite.rewrite_text(text, claude_profile)
        assert "${CLAUDE_PLUGIN_ROOT}/sdd/templates/DEFINE_TEMPLATE.md" in result

    def test_strips_absolute_prefix_with_token(self, claude_profile):
        text = "/Users/foo/agentspec/${CLAUDE_PLUGIN_ROOT}/skills/x/SKILL.md"
        result = path_rewrite.rewrite_text(text, claude_profile)
        assert result.startswith("${CLAUDE_PLUGIN_ROOT}/skills/")

    def test_empty_input_returns_empty(self, claude_profile):
        assert path_rewrite.rewrite_text("", claude_profile) == ""


class TestStaleReferences:
    def test_finds_unrewritten_paths(self, tmp_path, claude_profile):
        target = tmp_path / "doc.md"
        target.write_text("See .claude/agents/foo.md here\n", encoding="utf-8")
        findings = path_rewrite.stale_references(tmp_path, claude_profile)
        assert any("foo.md" in line for _, _, line in findings)

    def test_ignores_workspace_paths(self, tmp_path, claude_profile):
        target = tmp_path / "doc.md"
        target.write_text(
            "Outputs land in .claude/sdd/features/FEAT.md\n",
            encoding="utf-8",
        )
        findings = path_rewrite.stale_references(tmp_path, claude_profile)
        assert findings == []

    def test_ignores_lines_with_token(self, tmp_path, claude_profile):
        target = tmp_path / "doc.md"
        target.write_text(
            "See .claude/agents foo and ${CLAUDE_PLUGIN_ROOT}/agents/foo.md\n",
            encoding="utf-8",
        )
        findings = path_rewrite.stale_references(tmp_path, claude_profile)
        # Line contains the token, so it is treated as already migrated.
        assert findings == []


class TestRewriteFile:
    def test_changes_file_when_paths_present(self, tmp_path, claude_profile):
        f = tmp_path / "doc.md"
        f.write_text("See .claude/kb/dbt/index.md\n", encoding="utf-8")
        result = path_rewrite.rewrite_file(f, claude_profile)
        assert result.changed is True
        assert "${CLAUDE_PLUGIN_ROOT}/kb/dbt/index.md" in f.read_text(encoding="utf-8")

    def test_no_change_when_already_migrated(self, tmp_path, claude_profile):
        f = tmp_path / "doc.md"
        f.write_text("See ${CLAUDE_PLUGIN_ROOT}/kb/dbt/index.md\n", encoding="utf-8")
        result = path_rewrite.rewrite_file(f, claude_profile)
        assert result.changed is False
