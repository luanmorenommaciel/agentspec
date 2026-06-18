"""Unit tests for scripts/lib/packaging.py."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts.lib import packaging, platforms


@pytest.fixture
def fake_source(tmp_path):
    """Build a tiny source tree that mirrors .claude/ shape."""
    root = tmp_path / "src"
    (root / "agents" / "workflow").mkdir(parents=True)
    (root / "agents" / "workflow" / "build-agent.md").write_text(
        "---\nname: build-agent\n---\nbody\n", encoding="utf-8",
    )
    (root / "agents" / "workflow" / "_template.md").write_text("scaffold\n", encoding="utf-8")
    (root / "commands").mkdir()
    (root / "commands" / "define.md").write_text(
        "---\nname: define\n---\nbody\n", encoding="utf-8",
    )
    (root / "skills" / "agent-router").mkdir(parents=True)
    (root / "skills" / "agent-router" / "SKILL.md").write_text(
        "---\nname: agent-router\n---\n", encoding="utf-8",
    )
    (root / "kb" / "dbt").mkdir(parents=True)
    (root / "kb" / "dbt" / "index.md").write_text("# dbt\n", encoding="utf-8")
    (root / "kb" / "_templates").mkdir()
    return root


class TestCopySourceTree:
    def test_excludes_pycache(self, tmp_path):
        src = tmp_path / "src"
        (src / "__pycache__").mkdir(parents=True)
        (src / "__pycache__" / "foo.pyc").write_text("compiled")
        (src / "a.py").write_text("print('hi')")
        dest = tmp_path / "dest"
        packaging.copy_source_tree(src, dest)
        assert (dest / "a.py").exists()
        assert not (dest / "__pycache__").exists()

    def test_replaces_existing_destination(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.txt").write_text("new")
        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "stale.txt").write_text("stale")
        packaging.copy_source_tree(src, dest)
        assert (dest / "a.txt").read_text() == "new"
        assert not (dest / "stale.txt").exists()


class TestSummarize:
    def test_counts_artifacts_correctly(self, fake_source):
        profile = platforms.get_profile(platforms.CLAUDE)
        summary = packaging.summarize(profile, fake_source, results=[])
        # _template.md must be excluded from the agent count
        assert summary.agents == 1
        assert summary.commands == 1
        assert summary.skills == 1
        assert summary.kb_domains == 1   # _templates excluded


class TestRemoveWorkspaceDirs:
    def test_drops_features_reports_archive(self, tmp_path):
        plugin = tmp_path / "plugin"
        (plugin / "sdd" / "features").mkdir(parents=True)
        (plugin / "sdd" / "reports").mkdir()
        (plugin / "sdd" / "archive").mkdir()
        (plugin / "sdd" / "templates").mkdir()
        packaging.remove_workspace_dirs(plugin)
        assert not (plugin / "sdd" / "features").exists()
        assert not (plugin / "sdd" / "reports").exists()
        assert not (plugin / "sdd" / "archive").exists()
        # templates must survive
        assert (plugin / "sdd" / "templates").exists()
