"""Test suite for OpenCode compatibility layer.

Validates the build artifact produced by ``build-opencode.sh``.
Each test is a gate — the port task isn't "done" until its test passes.

Run with:  make test-opencode  (or: python3 -m pytest tests/test_opencode_compat.py -v)
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

# ── Path helpers ──────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENCODE_DIR = REPO_ROOT / ".opencode"
CLAUDE_AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
CLAUDE_COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"

# Valid OpenCode permission keys (from docs)
VALID_PERMISSION_KEYS = frozenset({
    "read", "edit", "glob", "grep", "list",
    "bash", "task", "todowrite", "webfetch", "websearch",
    "question", "skill", "lsp", "external_directory",
})

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _all_files(directory: Path, glob_pattern: str = "*.md") -> list[Path]:
    """Return all matching files in a directory, excluding README files."""
    if not directory.exists():
        return []
    files = list(directory.rglob(glob_pattern))
    return [f for f in files if f.name not in ("README.md", "_template.md")]


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML-ish frontmatter as a raw dict (regex, no PyYAML)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    body = m.group(1)
    fm: dict[str, str] = {}
    for line in body.splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def _parse_frontmatter_multiline(text: str) -> dict[str, object]:
    """Extract YAML-ish frontmatter, preserving block scalars."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    body = m.group(1)
    fm: dict[str, object] = {}

    # Simple scalar keys
    for key in ("name", "mode", "model", "tier", "color", "agent"):
        match = re.search(rf"^{key}:\s*(.+)$", body, re.MULTILINE)
        if match:
            fm[key] = match.group(1).strip()

    # description (block scalar |)
    m_desc = re.search(r"^description:\s*\|\s*\n((?:[ \t]+.*\n?)+)", body, re.MULTILINE)
    if m_desc:
        fm["description"] = m_desc.group(1)
    else:
        m_desc = re.search(r"^description:\s*(.+)$", body, re.MULTILINE)
        if m_desc:
            fm["description"] = m_desc.group(1).strip()

    # permission block — extract keys
    perm_match = re.search(r"^permission:\s*\n((?:[ \t]+\w+:\s*\w+\n?)+)", body, re.MULTILINE)
    if perm_match:
        perm_raw = perm_match.group(1)
        perm_dict: dict[str, str] = {}
        for line in perm_raw.splitlines():
            pline = line.strip()
            if ":" in pline:
                pk, _, pv = pline.partition(":")
                perm_dict[pk.strip()] = pv.strip()
        fm["_permission"] = perm_dict

    # tools list
    m_tools = re.search(r"^tools:\s*\[([^\]]*)\]", body, re.MULTILINE)
    if m_tools:
        items = [s.strip().strip("\"'") for s in m_tools.group(1).split(",") if s.strip()]
        fm["_tools"] = items

    return fm


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _require_build(func):
    """Decorator: skip the test if .opencode/ hasn't been built yet."""
    return pytest.mark.skipif(
        not OPENCODE_DIR.exists() or not list(OPENCODE_DIR.rglob("*.md")),
        reason=".opencode/ not built yet — run 'make build-opencode' first",
    )(func)


# ══════════════════════════════════════════════════════════════════════════════
# TASK-002 — Agents
# ══════════════════════════════════════════════════════════════════════════════


class TestAgentStructure:
    """Structural integrity of .opencode/agents/."""

    @_require_build
    def test_agent_directory_exists(self):
        agents_dir = OPENCODE_DIR / "agents"
        assert agents_dir.exists(), ".opencode/agents/ does not exist"
        assert agents_dir.is_dir(), ".opencode/agents/ is not a directory"

    @_require_build
    def test_agent_count_matches_claude(self):
        """Every agent in .claude/agents/ has a counterpart in .opencode/agents/."""
        claude_agents = _all_files(CLAUDE_AGENTS_DIR)
        opencode_agents = _all_files(OPENCODE_DIR / "agents")
        assert len(opencode_agents) == len(claude_agents), (
            f"Agent count mismatch: {len(opencode_agents)} in .opencode/ "
            f"vs {len(claude_agents)} in .claude/"
        )

    @_require_build
    def test_agent_rel_paths_match(self):
        """The relative file structure mirrors .claude/agents/."""
        claude_paths = {
            str(f.relative_to(CLAUDE_AGENTS_DIR))
            for f in _all_files(CLAUDE_AGENTS_DIR)
        }
        opencode_paths = {
            str(f.relative_to(OPENCODE_DIR / "agents"))
            for f in _all_files(OPENCODE_DIR / "agents")
        }
        missing = claude_paths - opencode_paths
        assert not missing, f"OpenCode agents missing: {missing}"
        extra = opencode_paths - claude_paths
        assert not extra, f"OpenCode agents extra: {extra}"

    @_require_build
    def test_agent_categories_preserved(self):
        """All 8 agent categories are present."""
        expected_categories = {
            "architect", "cloud", "data-engineering",
            "dev", "platform", "python", "test", "workflow",
        }
        actual = {
            d.name for d in (OPENCODE_DIR / "agents").iterdir() if d.is_dir()
        }
        assert actual == expected_categories, (
            f"Category mismatch: got {sorted(actual)}, expected {sorted(expected_categories)}"
        )


class TestAgentFrontmatter:
    """Frontmatter validation for .opencode/ agent files."""

    @_require_build
    @pytest.mark.parametrize("agent_file", [])
    def test_agent_has_name(self, agent_file: Path):
        fm = _parse_frontmatter(agent_file.read_text(encoding="utf-8"))
        assert fm.get("name"), f"Missing 'name' in {agent_file}"

    @_require_build
    def test_all_agents_have_permission_block(self):
        """Every OpenCode agent must have a permission: block."""
        missing = []
        for f in _all_files(OPENCODE_DIR / "agents"):
            fm = _parse_frontmatter_multiline(f.read_text(encoding="utf-8"))
            if not fm.get("_permission"):
                missing.append(str(f.relative_to(OPENCODE_DIR)))
        assert not missing, f"Agents missing permission: block: {missing}"

    @_require_build
    def test_all_agents_have_mode_subagent(self):
        """Every OpenCode agent must have mode: subagent."""
        missing = []
        for f in _all_files(OPENCODE_DIR / "agents"):
            fm = _parse_frontmatter_multiline(f.read_text(encoding="utf-8"))
            if fm.get("mode") != "subagent":
                missing.append(str(f.relative_to(OPENCODE_DIR)))
        assert not missing, f"Agents missing mode: subagent: {missing}"

    @_require_build
    def test_permission_keys_are_valid(self):
        """All permission keys must be valid OpenCode keys."""
        invalid = []
        for f in _all_files(OPENCODE_DIR / "agents"):
            fm = _parse_frontmatter_multiline(f.read_text(encoding="utf-8"))
            perms: dict = fm.get("_permission", {})  # type: ignore[assignment]
            for pk in perms:
                if pk not in VALID_PERMISSION_KEYS:
                    invalid.append(
                        f"{f.relative_to(OPENCODE_DIR)}: unknown key '{pk}'"
                    )
        assert not invalid, "Invalid permission keys:\n" + "\n".join(invalid)

    @_require_build
    def test_no_mcp_in_opencode_permission_block(self):
        """No mcp__ references in OpenCode permission: blocks (only tools: field may have them)."""
        violations = []
        mcp_re = re.compile(r"mcp__", re.IGNORECASE)
        for f in _all_files(OPENCODE_DIR / "agents"):
            fm = _parse_frontmatter_multiline(f.read_text(encoding="utf-8"))
            perms: dict = fm.get("_permission", {})  # type: ignore[assignment]
            for pk in perms:
                if mcp_re.search(pk):
                    violations.append(f"{f.relative_to(OPENCODE_DIR)}: permission key '{pk}'")
        assert not violations, f"mcp__ references in permission: block: {violations}"

    @_require_build
    def test_tools_field_stripped_for_opencode(self):
        """tools: field is intentionally removed — OpenCode rejects the list format."""
        violations = []
        for f in _all_files(OPENCODE_DIR / "agents"):
            fm = _parse_frontmatter_multiline(f.read_text(encoding="utf-8"))
            if fm.get("_tools"):
                violations.append(str(f.relative_to(OPENCODE_DIR)))
        assert not violations, (
            f"Agents with stale tools: field (should be stripped): {violations}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TASK-003 — Commands
# ══════════════════════════════════════════════════════════════════════════════


class TestCommandStructure:
    """Structural integrity of .opencode/commands/."""

    @_require_build
    def test_command_directory_exists(self):
        assert (OPENCODE_DIR / "commands").is_dir()

    @_require_build
    def test_command_count_matches_claude(self):
        claude_cmds = _all_files(CLAUDE_COMMANDS_DIR)
        opencode_cmds = _all_files(OPENCODE_DIR / "commands")
        assert len(opencode_cmds) == len(claude_cmds), (
            f"Command count mismatch: {len(opencode_cmds)} vs {len(claude_cmds)}"
        )

    @_require_build
    @pytest.mark.parametrize("cmd_relative", [
        # Workflow — must exist
        "workflow/brainstorm.md", "workflow/define.md", "workflow/design.md",
        "workflow/build.md", "workflow/ship.md", "workflow/iterate.md",
        "workflow/create-pr.md",
        # Data engineering
        "data-engineering/pipeline.md", "data-engineering/schema.md",
        "data-engineering/data-quality.md", "data-engineering/lakehouse.md",
        "data-engineering/sql-review.md", "data-engineering/ai-pipeline.md",
        "data-engineering/data-contract.md", "data-engineering/migrate.md",
        # Review
        "review/judge.md", "review/review.md",
        # Core
        "core/status.md", "core/memory.md", "core/meeting.md",
        "core/sync-context.md", "core/readme-maker.md",
        # Visual explainer
        "visual-explainer/generate-web-diagram.md",
        "visual-explainer/generate-slides.md",
        "visual-explainer/generate-visual-plan.md",
        "visual-explainer/diff-review.md",
        "visual-explainer/plan-review.md",
        "visual-explainer/project-recap.md",
        "visual-explainer/fact-check.md",
        "visual-explainer/share.md",
        # Knowledge
        "knowledge/create-kb.md",
    ])
    def test_known_command_exists(self, cmd_relative: str):
        path = OPENCODE_DIR / "commands" / cmd_relative
        assert path.exists(), f"Missing command: {cmd_relative}"


class TestCommandNoStaleRefs:
    """No Claude Code-specific references in .opencode/commands/."""

    @_require_build
    def test_no_claude_plugin_root(self):
        """No ${CLAUDE_PLUGIN_ROOT} in OpenCode command files."""
        violations = []
        for f in _all_files(OPENCODE_DIR / "commands"):
            text = f.read_text(encoding="utf-8")
            if "${CLAUDE_PLUGIN_ROOT" in text:
                violations.append(str(f.relative_to(OPENCODE_DIR)))
        assert not violations, (
            f"Commands with ${CLAUDE_PLUGIN_ROOT}: {violations}"
        )

    @_require_build
    def test_no_agentspec_prefix(self):
        """No /agentspec: prefix in OpenCode command files."""
        violations = []
        for f in _all_files(OPENCODE_DIR / "commands"):
            text = f.read_text(encoding="utf-8")
            if "/agentspec:" in text:
                violations.append(str(f.relative_to(OPENCODE_DIR)))
        assert not violations, (
            f"Commands with /agentspec: prefix: {violations}"
        )

    @_require_build
    def test_opencode_commands_have_description(self):
        """Every OpenCode command has a name or description field."""
        missing = []
        for f in _all_files(OPENCODE_DIR / "commands"):
            fm = _parse_frontmatter(f.read_text(encoding="utf-8"))
            if not fm.get("name") and not fm.get("description"):
                missing.append(str(f.relative_to(OPENCODE_DIR)))
        assert not missing, f"Commands missing name/description: {missing}"


# ══════════════════════════════════════════════════════════════════════════════
# TASK-004 — Skills
# ══════════════════════════════════════════════════════════════════════════════


class TestSkills:
    """OpenCode skill files."""

    @_require_build
    def test_skills_directory_exists(self):
        assert (OPENCODE_DIR / "skills").is_dir()

    @_require_build
    def test_skills_have_required_skills(self):
        """Core skills must be present."""
        required = {"agent-router", "visual-explainer", "excalidraw-diagram",
                     "sdd-workflow", "data-engineering-guide"}
        skill_dirs = {
            d.name for d in (OPENCODE_DIR / "skills").iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        }
        missing = required - skill_dirs
        assert not missing, f"Missing skills: {missing}"

    @_require_build
    def test_no_agentspec_prefix_in_skills(self):
        """Skills must reference commands without /agentspec: namespace."""
        violations = []
        for f in _all_files(OPENCODE_DIR / "skills", "SKILL.md"):
            text = f.read_text(encoding="utf-8")
            if "/agentspec:" in text:
                violations.append(str(f.relative_to(OPENCODE_DIR)))
        assert not violations, f"Skills with /agentspec: prefix: {violations}"

    @_require_build
    def test_skills_have_name(self):
        """Every SKILL.md has frontmatter name."""
        missing = []
        for f in _all_files(OPENCODE_DIR / "skills", "SKILL.md"):
            fm = _parse_frontmatter(f.read_text(encoding="utf-8"))
            if not fm.get("name"):
                missing.append(str(f.relative_to(OPENCODE_DIR)))
        assert not missing, f"Skills missing name: {missing}"


# ══════════════════════════════════════════════════════════════════════════════
# TASK-005 — Judge script
# ══════════════════════════════════════════════════════════════════════════════


class TestJudgeStorage:
    """judge.py ledger path logic."""

    def test_judge_has_opencode_storage_constant(self):
        """judge.py defines OPENCODE_LEDGER or equivalent parallel path."""
        judge_path = REPO_ROOT / "scripts" / "judge.py"
        text = judge_path.read_text(encoding="utf-8")
        assert ".opencode" in text, (
            "judge.py must reference .opencode/storage/ for OpenCode compatibility"
        )

    def test_judge_has_claude_storage_for_fallback(self):
        """judge.py keeps original .claude/storage/ path."""
        judge_path = REPO_ROOT / "scripts" / "judge.py"
        text = judge_path.read_text(encoding="utf-8")
        assert ".claude" in text, (
            "judge.py must keep .claude/storage/ fallback"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TASK-006 — Agent Router
# ══════════════════════════════════════════════════════════════════════════════


class TestAgentRouter:
    """generate-agent-router.py OpenCode compatibility."""

    def test_router_references_opencode_paths(self):
        """The router script should have .opencode/ path constants."""
        router_path = REPO_ROOT / "scripts" / "generate-agent-router.py"
        text = router_path.read_text(encoding="utf-8")
        assert ".opencode" in text, (
            "generate-agent-router.py must reference .opencode/ paths"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TASK-007 — Plugin
# ══════════════════════════════════════════════════════════════════════════════


class TestPlugin:
    """Init workspace plugin stub."""

    @_require_build
    def test_plugin_directory_exists(self):
        assert (OPENCODE_DIR / "plugins").is_dir()

    @_require_build
    def test_init_workspace_plugin_exists(self):
        plugin = OPENCODE_DIR / "plugins" / "init-workspace.js"
        assert plugin.exists(), "init-workspace.js plugin not found"

    @_require_build
    def test_init_workspace_is_valid_js(self):
        """The JS file is syntactically valid."""
        plugin = OPENCODE_DIR / "plugins" / "init-workspace.js"
        text = plugin.read_text(encoding="utf-8")
        # Must export a function
        assert "export" in text, "Plugin must export a function"


# ══════════════════════════════════════════════════════════════════════════════
# TASK-012 — Config
# ══════════════════════════════════════════════════════════════════════════════


class TestOpenCodeConfig:
    """opencode.json validation."""

    @_require_build
    def test_opencode_json_exists(self):
        assert (OPENCODE_DIR / "opencode.json").exists()

    @_require_build
    def test_opencode_json_is_valid(self):
        cfg_path = OPENCODE_DIR / "opencode.json"
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            pytest.fail(f"opencode.json is not valid JSON: {e}")
        assert isinstance(data, dict)

    @_require_build
    def test_opencode_json_has_schema(self):
        cfg_path = OPENCODE_DIR / "opencode.json"
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert "$schema" in data, "opencode.json missing $schema"


# ══════════════════════════════════════════════════════════════════════════════
# TASK-008 — AGENTS.md
# ══════════════════════════════════════════════════════════════════════════════


class TestAgentsMd:
    """AGENTS.md project rules file."""

    def test_agents_md_exists(self):
        agents_md = REPO_ROOT / "AGENTS.md"
        assert agents_md.exists(), (
            "AGENTS.md does not exist — create it with OpenCode project rules"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Structural / Integrity
# ══════════════════════════════════════════════════════════════════════════════


class TestOverallStructure:
    """Top-level .opencode/ directory structure."""

    @_require_build
    def test_opencode_directory_structure(self):
        """All expected subdirectories exist after build."""
        expected = {"agents", "commands", "skills", "plugins", "sdd"}
        actual = {
            d.name for d in OPENCODE_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        }
        missing = expected - actual
        assert not missing, f"Missing directories: {missing}"

    @_require_build
    def test_agent_categories_are_subdirs(self):
        """Agents are organized into category subdirectories."""
        agents_root = OPENCODE_DIR / "agents"
        subdirs = [d for d in agents_root.iterdir() if d.is_dir()]
        assert len(subdirs) >= 8, f"Expected >=8 agent categories, got {len(subdirs)}"

    @_require_build
    def test_sdd_templates_exist(self):
        """SDD phase templates are included in .opencode/sdd/templates/."""
        templates_dir = OPENCODE_DIR / "sdd" / "templates"
        assert templates_dir.is_dir(), "Missing .opencode/sdd/templates/"
        expected = {
            "BRAINSTORM_TEMPLATE.md", "DEFINE_TEMPLATE.md",
            "DESIGN_TEMPLATE.md", "BUILD_REPORT_TEMPLATE.md",
            "SHIPPED_TEMPLATE.md",
        }
        actual = {f.name for f in templates_dir.iterdir() if f.suffix == ".md"}
        missing = expected - actual
        assert not missing, f"Missing templates: {missing}"

    @_require_build
    def test_opensource_claude_sources_untouched(self):
        """The .claude/ directory is not modified by the build."""
        # Check that .claude/ still has its original structure
        assert (CLAUDE_AGENTS_DIR).exists(), ".claude/agents/ should still exist"
        assert (CLAUDE_COMMANDS_DIR).exists(), ".claude/commands/ should still exist"

    @_require_build
    def test_no_agent_body_text_divergence(self):
        """Agent body text (below frontmatter) matches between .claude/ and .opencode/."""
        diverged = []
        for claude_file in _all_files(CLAUDE_AGENTS_DIR):
            rel = claude_file.relative_to(CLAUDE_AGENTS_DIR)
            opencode_file = OPENCODE_DIR / "agents" / rel

            if not opencode_file.exists():
                continue

            claude_text = claude_file.read_text(encoding="utf-8")
            opencode_text = opencode_file.read_text(encoding="utf-8")

            # Compare body (after frontmatter)
            claude_body = FRONTMATTER_RE.sub("", claude_text)
            opencode_body = FRONTMATTER_RE.sub("", opencode_text)

            if claude_body != opencode_body:
                diverged.append(str(rel))
                # Show first diff
                if len(diverged) <= 3:  # Limit to avoid spam
                    for i, (cl, oc) in enumerate(zip(
                        claude_body.splitlines(),
                        opencode_body.splitlines()
                    )):
                        if cl != oc:
                            diverged.append(f"  Line {i+1}: '{cl[:80]}' vs '{oc[:80]}'")
                            break

        assert not diverged, f"Agent body text diverges in: {diverged[:5]}"
