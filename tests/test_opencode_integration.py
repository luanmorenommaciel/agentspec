"""Integration tests against a live ``opencode serve`` instance.

Validates that OpenCode discovers and correctly parses our built
``.opencode/`` artifact.

Run with:  make test-opencode-integration  (builds + tests against live opencode)
"""
from __future__ import annotations

import pytest

# Tell pytest to load the conftest_opencode module so the fixture is available
pytest_plugins = ["tests.conftest_opencode"]

# ── Expected constants ────────────────────────────────────────────────────────

EXPECTED_AGENT_NAMES = frozenset({
    "dbt-specialist", "build-agent", "pipeline-architect", "schema-designer",
    "spark-engineer", "sql-optimizer", "airflow-specialist",
    "brainstorm-agent", "define-agent", "design-agent", "ship-agent",
    "iterate-agent", "data-quality-analyst", "data-contracts-engineer",
    "spark-specialist", "streaming-engineer", "lakehouse-architect",
    "medallion-architect", "data-platform-engineer", "genai-architect",
    "kb-architect", "the-planner", "lakeflow-specialist", "lakeflow-expert",
    "lakeflow-architect", "lakeflow-pipeline-builder", "qdrant-specialist",
    "ai-data-engineer", "ai-data-engineer-cloud", "ai-data-engineer-gcp",
    "ai-prompt-specialist", "ai-prompt-specialist-gcp",
    "spark-streaming-architect", "spark-performance-analyzer",
    "spark-troubleshooter", "fabric-architect", "fabric-ai-specialist",
    "fabric-cicd-specialist", "fabric-logging-specialist",
    "fabric-pipeline-developer", "fabric-security-specialist",
    "aws-data-architect", "aws-deployer", "aws-lambda-architect",
    "ci-cd-specialist", "lambda-builder", "gcp-data-architect",
    "supabase-specialist", "code-reviewer", "python-developer",
    "code-cleaner", "code-documenter", "llm-specialist",
    "test-generator", "codebase-explorer", "meeting-analyst",
    "prompt-crafter", "shell-script-specialist",
})

EXPECTED_COMMAND_NAMES = frozenset({
    # Workflow
    "brainstorm", "define", "design", "build", "ship", "iterate", "create-pr",
    # Data engineering
    "pipeline", "schema", "data-quality", "lakehouse", "sql-review",
    "ai-pipeline", "data-contract", "migrate",
    # Review
    "judge", "review",
    # Core
    "status", "memory", "meeting", "sync-context", "readme-maker",
    # Visual explainer — OpenCode preserves directory as namespace prefix
    "visual-explainer/generate-web-diagram", "visual-explainer/generate-slides",
    "visual-explainer/generate-visual-plan", "visual-explainer/diff-review",
    "visual-explainer/plan-review", "visual-explainer/project-recap",
    "visual-explainer/fact-check", "share",
    # Knowledge
    "create-kb",
})


# ══════════════════════════════════════════════════════════════════════════════
# Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestServerHealth:
    """Verify the opencode server starts and responds."""

    def test_server_is_healthy(self, opencode_server):
        health = opencode_server.get_health()
        assert health.get("healthy") is True, f"Server not healthy: {health}"
        assert "version" in health, "Health response missing version"


class TestAgentDiscovery:
    """Verify our custom agents are loaded by OpenCode."""

    def test_custom_agent_count(self, opencode_server):
        agents = opencode_server.get_agents()
        custom = [a for a in agents if not a.get("native")]
        assert len(custom) >= 58, (
            f"Expected >=58 custom agents, got {len(custom)}"
        )

    def test_known_agent_names(self, opencode_server):
        agents = opencode_server.get_agents()
        custom_names = {a["name"] for a in agents if not a.get("native")}
        # Filter out non-agent items (README.md, etc.)
        agent_only = {n for n in custom_names if not n.isupper() and n != "README"}
        missing = EXPECTED_AGENT_NAMES - agent_only
        assert not missing, f"Missing agents: {sorted(missing)}"

    def test_non_native_agents_are_not_primary(self, opencode_server):
        """No custom agent should accidentally register as a primary agent."""
        agents = opencode_server.get_agents()
        custom_primaries = [
            a["name"] for a in agents
            if not a.get("native") and a.get("mode") == "primary"
        ]
        assert not custom_primaries, (
            f"Custom agents registered as primary: {custom_primaries}"
        )

    def test_custom_agents_have_mode_subagent(self, opencode_server):
        """Custom agents should register as subagent mode."""
        agents = opencode_server.get_agents()
        non_subagent = []
        for a in agents:
            if a.get("native"):
                continue
            name = a["name"]
            # Skip README (non-agent markdown file)
            if name in ("README",) or name.isupper():
                continue
            if a.get("mode") != "subagent":
                non_subagent.append(f"{name} (mode={a.get('mode')})")
        assert not non_subagent, (
            f"Custom agents with wrong mode: {non_subagent}"
        )

    def test_agent_permissions_present(self, opencode_server):
        """Custom agents should have permission entries."""
        agents = opencode_server.get_agents()
        without_perms = []
        for a in agents:
            if a.get("native"):
                continue
            name = a["name"]
            if name in ("README",) or name.isupper():
                continue
            if not a.get("permission"):
                without_perms.append(name)
        assert not without_perms, (
            f"Custom agents missing permissions: {without_perms}"
        )


class TestCommandDiscovery:
    """Verify our custom commands are loaded by OpenCode."""

    def test_known_commands_present(self, opencode_server):
        commands = opencode_server.get_commands()
        found_names = {c["name"] for c in commands}
        missing = EXPECTED_COMMAND_NAMES - found_names
        assert not missing, f"Missing commands: {sorted(missing)}"

    def test_commands_have_template(self, opencode_server):
        """Every custom command should have a template (body content)."""
        commands = opencode_server.get_commands()
        without_template = []
        for c in commands:
            if c["name"] not in EXPECTED_COMMAND_NAMES:
                continue
            if not c.get("template"):
                without_template.append(c["name"])
        assert not without_template, (
            f"Custom commands without template: {without_template}"
        )


class TestConfigLoading:
    """Verify opencode.json and project rules are loaded."""

    def test_config_loads_without_error(self, opencode_server):
        """GET /config should return valid data (not an error)."""
        config = opencode_server.get_config()
        assert isinstance(config, dict), f"Config is not a dict: {type(config)}"
        # If there's a $schema, it loaded successfully
        assert config, "Config is empty — opencode.json not loaded"

    def test_no_config_startup_errors(self, opencode_server):
        """Stderr should NOT contain ConfigInvalidError or SchemaError."""
        assert not opencode_server.has_stderr_line("ConfigInvalidError"), (
            "ConfigInvalidError in server stderr"
        )
        assert not opencode_server.has_stderr_line("SchemaError"), (
            "SchemaError in server stderr"
        )


class TestSkillDiscovery:
    """Verify skills are loaded from .opencode/skills/."""

    def test_skill_count(self, opencode_server):
        """Skills should be loaded (check skill count in config or server init log)."""
        # Skills appear in the server init log as "skill count=N init"
        assert opencode_server.has_stderr_line("skill count="), (
            "Skills not loaded — missing 'skill count=' in server logs"
        )
