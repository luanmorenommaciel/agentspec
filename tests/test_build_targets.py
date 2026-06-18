"""Snapshot-style tests for the dist/ outputs.

These tests build each target into a temporary dist directory and assert
shape invariants (counts, manifest fields, judge.py presence). They are
deliberately fast — counts only, no content snapshots — because the full
build runs in ~1 second.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(script: str) -> None:
    result = subprocess.run(
        [sys.executable, f"scripts/{script}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Build failed: {script}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.fixture(scope="module", autouse=True)
def build_all():
    """Build every target once for the whole module."""
    # The orchestrator runs every per-platform builder.
    result = subprocess.run(
        [sys.executable, "scripts/build_all.py"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"build-all failed:\n{result.stdout}\n{result.stderr}"
    yield


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestClaude:
    def test_manifest_exists(self):
        manifest = _read_json(REPO_ROOT / "dist" / "claude" / ".claude-plugin" / "plugin.json")
        assert manifest["name"] == "agentspec"
        assert "version" in manifest

    def test_marketplace_exists(self):
        market = _read_json(REPO_ROOT / "dist" / "claude" / ".claude-plugin" / "marketplace.json")
        assert market["name"] == "agentspec"
        assert market["plugins"]

    def test_judge_shipped(self):
        assert (REPO_ROOT / "dist" / "claude" / "scripts" / "judge.py").exists()

    def test_build_report(self):
        report = _read_json(REPO_ROOT / "dist" / "claude" / "build-report.json")
        assert report["agents"] >= 50
        assert report["commands"] >= 25
        assert report["kb_domains"] >= 20


class TestCursor:
    def test_cursor_manifest_exists(self):
        manifest = _read_json(REPO_ROOT / "dist" / "cursor" / ".cursor-plugin" / "plugin.json")
        assert manifest["name"] == "agentspec"

    def test_claude_format_mirror(self):
        manifest = _read_json(REPO_ROOT / "dist" / "cursor" / ".claude-plugin" / "plugin.json")
        assert manifest["name"] == "agentspec"

    def test_skills_include_converted_commands(self):
        skill_dir = REPO_ROOT / "dist" / "cursor" / "skills"
        define = skill_dir / "define" / "SKILL.md"
        assert define.exists()
        content = define.read_text(encoding="utf-8")
        assert "disable-model-invocation: true" in content


class TestCopilot:
    def test_workspace_prompts_emitted(self):
        prompts = REPO_ROOT / "dist" / "vscode-copilot" / ".github" / "prompts"
        assert prompts.exists()
        files = list(prompts.glob("*.prompt.md"))
        assert len(files) >= 25

    def test_workflow_agent_has_handoff(self):
        agent = REPO_ROOT / "dist" / "vscode-copilot" / ".github" / "agents" / "define-agent.agent.md"
        assert agent.exists()
        content = agent.read_text(encoding="utf-8")
        assert "handoffs:" in content
        assert "design-agent" in content


class TestMcp:
    def test_mcp_config_exists(self):
        config = _read_json(REPO_ROOT / "dist" / "mcp" / "mcp.json")
        assert "agentspec-mcp" in config["mcpServers"]

    def test_server_package_shipped(self):
        assert (REPO_ROOT / "dist" / "mcp" / "server" / "agentspec_mcp" / "__main__.py").exists()

    def test_routing_json_shipped(self):
        routing = REPO_ROOT / "dist" / "mcp" / "resources" / "skills" / "agent-router" / "routing.json"
        assert routing.exists()
        data = _read_json(routing)
        assert data["agent_count"] >= 50
