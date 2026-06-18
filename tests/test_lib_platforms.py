"""Unit tests for scripts/lib/platforms.py."""
from __future__ import annotations

import pytest

from scripts.lib import platforms


class TestPlatformProfile:
    def test_all_platform_ids_resolve(self):
        for pid in platforms.ALL_PLATFORMS:
            profile = platforms.get_profile(pid)
            assert profile.id == pid

    def test_unknown_platform_raises(self):
        with pytest.raises(KeyError) as exc:
            platforms.get_profile("not-a-platform")
        assert "Unknown platform" in str(exc.value)

    def test_claude_keeps_namespace(self):
        profile = platforms.get_profile(platforms.CLAUDE)
        assert profile.namespace == "agentspec"
        assert profile.root_token == "${CLAUDE_PLUGIN_ROOT}"

    def test_cursor_has_no_namespace(self):
        profile = platforms.get_profile(platforms.CURSOR)
        assert profile.namespace == ""
        assert profile.root_token == "${PLUGIN_ROOT}"

    def test_copilot_uses_claude_token(self):
        """VS Code Agent Plugins auto-detect Claude-format manifests."""
        profile = platforms.get_profile(platforms.COPILOT)
        assert profile.root_token == "${CLAUDE_PLUGIN_ROOT}"
        assert profile.manifest_dir == ".claude-plugin"

    def test_mcp_has_resources_layout(self):
        profile = platforms.get_profile(platforms.MCP)
        assert profile.skill_root == "resources/skills"
        assert profile.kb_root == "resources/kb"
        assert profile.hooks_path == ""

    def test_workspace_paths_are_consistent(self):
        for pid in platforms.ALL_PLATFORMS:
            profile = platforms.get_profile(pid)
            # Workspace paths must always include the SDD output directories
            assert ".claude/sdd/features" in profile.workspace_paths
            assert ".claude/sdd/reports" in profile.workspace_paths
            assert ".claude/sdd/archive" in profile.workspace_paths

    def test_dist_root_uses_output_subdir(self, tmp_path):
        for pid in platforms.ALL_PLATFORMS:
            profile = platforms.get_profile(pid)
            assert platforms.dist_root(tmp_path, pid).name == profile.output_subdir
