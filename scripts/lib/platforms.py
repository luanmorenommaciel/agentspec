"""Platform profiles for the AgentSpec multi-target build.

Author: Emerson Antonio
Date: 2026-06-17

Each profile declares everything the builder needs to know about a target
runtime: where the plugin manifest lives, which root token to use in paths,
which slash-command namespace (if any) applies, and which workspace paths
must NOT be rewritten because they belong to the user's project.

Profiles are intentionally declarative — no behavior — so we can test them
in isolation and so per-platform builders consume the same surface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


# ── Platform identifiers ─────────────────────────────────────────────────────

CLAUDE = "claude"
CURSOR = "cursor"
COPILOT = "vscode-copilot"
MCP = "mcp"

ALL_PLATFORMS: tuple[str, ...] = (CLAUDE, CURSOR, COPILOT, MCP)


# ── Profile dataclass ────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class PlatformProfile:
    """Declarative description of a build target.

    Frozen + slots so profiles behave as pure value objects — they cannot
    mutate after import, and the per-instance overhead stays small.
    """

    id: str                              # canonical platform id
    label: str                           # human-readable label
    output_subdir: str                   # path under dist/ for this target
    root_token: str                      # path token used in shipped artifacts
    manifest_dir: str                    # where the plugin manifest lives
    namespace: str                       # slash-command namespace (may be "")
    skill_root: str                      # plugin-internal skills directory
    agent_root: str                      # plugin-internal agents directory
    command_root: str                    # plugin-internal commands directory
    kb_root: str                         # plugin-internal KB directory
    sdd_root: str                        # plugin-internal SDD shared directory
    hooks_path: str                      # hooks config path inside the bundle
    mcp_config: str                      # mcp config path inside the bundle
    notes: str = ""                      # short freeform description

    # Workspace paths that MUST NOT be rewritten — they point to the user's
    # project regardless of where the plugin is installed.
    workspace_paths: tuple[str, ...] = (
        ".claude/sdd/features",
        ".claude/sdd/reports",
        ".claude/sdd/archive",
        ".claude/storage",
        ".claude/settings",
        ".claude/plans",
        ".claude/memory",
    )

    extras: Mapping[str, str] = field(default_factory=dict)


# ── Built-in profiles ────────────────────────────────────────────────────────

# Claude Code remains the source-format target. The current plugin/ output
# stays valid; dist/claude/ is an additional, isolated build for parity with
# the other targets.
CLAUDE_PROFILE = PlatformProfile(
    id=CLAUDE,
    label="Claude Code Plugin",
    output_subdir="claude",
    root_token="${CLAUDE_PLUGIN_ROOT}",
    manifest_dir=".claude-plugin",
    namespace="agentspec",
    skill_root="skills",
    agent_root="agents",
    command_root="commands",
    kb_root="kb",
    sdd_root="sdd",
    hooks_path="hooks/hooks.json",
    mcp_config=".mcp.json",
    notes="Native Claude Code plugin. Full-fidelity target.",
)

# Cursor uses .cursor-plugin manifests but also accepts Claude-format
# manifests for cross-tool plugins. We emit both for safety.
CURSOR_PROFILE = PlatformProfile(
    id=CURSOR,
    label="Cursor Plugin",
    output_subdir="cursor",
    root_token="${PLUGIN_ROOT}",
    manifest_dir=".cursor-plugin",
    namespace="",                        # Cursor invokes /define directly
    skill_root="skills",
    agent_root="agents",
    command_root="commands",
    kb_root="kb",
    sdd_root="sdd",
    hooks_path="hooks/hooks.json",
    mcp_config=".mcp.json",
    notes="Cursor plugin. Installs via marketplace or ~/.cursor/plugins/local/.",
)

# VS Code + Copilot Agent Plugins auto-detect Claude-format manifests too;
# we ship Claude-format paths so hooks and ${CLAUDE_PLUGIN_ROOT} remain valid
# while also providing .github/prompts and .github/agents workspace fallbacks.
COPILOT_PROFILE = PlatformProfile(
    id=COPILOT,
    label="VS Code + Copilot Agent Plugin",
    output_subdir="vscode-copilot",
    root_token="${CLAUDE_PLUGIN_ROOT}",   # Claude-format recognition by VS Code
    manifest_dir=".claude-plugin",
    namespace="",
    skill_root="skills",
    agent_root="agents",
    command_root="commands",
    kb_root="kb",
    sdd_root="sdd",
    hooks_path="hooks/hooks.json",
    mcp_config=".mcp.json",
    extras={
        "workspace_prompts_dir": ".github/prompts",
        "workspace_agents_dir": ".github/agents",
    },
    notes="VS Code Agent Plugin (preview). Requires chat.plugins.enabled.",
)

# MCP-only target ships KB, routing, judge and SDD status as MCP tools.
# No slash commands or agents are shipped here; this is the parity layer for
# any MCP-capable client.
MCP_PROFILE = PlatformProfile(
    id=MCP,
    label="AgentSpec MCP Server",
    output_subdir="mcp",
    root_token="${AGENTSPEC_ROOT}",
    manifest_dir="",
    namespace="",
    skill_root="resources/skills",
    agent_root="resources/agents",
    command_root="resources/commands",
    kb_root="resources/kb",
    sdd_root="resources/sdd",
    hooks_path="",
    mcp_config="mcp.json",
    notes="Universal MCP server. KB search, agent routing, judge, SDD status.",
)


PROFILES: dict[str, PlatformProfile] = {
    CLAUDE: CLAUDE_PROFILE,
    CURSOR: CURSOR_PROFILE,
    COPILOT: COPILOT_PROFILE,
    MCP: MCP_PROFILE,
}


# ── Lookup helpers ───────────────────────────────────────────────────────────

def get_profile(platform_id: str) -> PlatformProfile:
    """Return the profile for ``platform_id`` or raise ``KeyError``.

    Centralizing the lookup keeps every caller honest about which platforms
    exist and gives us a single place to evolve naming later.
    """
    try:
        return PROFILES[platform_id]
    except KeyError as exc:
        valid = ", ".join(sorted(PROFILES))
        raise KeyError(f"Unknown platform '{platform_id}'. Valid: {valid}") from exc


def dist_root(repo_root: Path, platform_id: str) -> Path:
    """Where artifacts for this platform are written."""
    profile = get_profile(platform_id)
    return repo_root / "dist" / profile.output_subdir
