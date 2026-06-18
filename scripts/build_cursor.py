#!/usr/bin/env python3
"""Build the Cursor distribution under ``dist/cursor/``.

Author: Emerson Antonio
Date: 2026-06-17

Cursor accepts Claude-format plugins and also has its own ``.cursor-plugin``
manifest. We ship both so the bundle can be installed via the Cursor
Marketplace, dropped into ``~/.cursor/plugins/local/`` for local development,
or referenced as a Claude-format plugin from settings.

Cursor-specific adaptations:
- ``${CLAUDE_PLUGIN_ROOT}`` is rewritten to the generic ``${PLUGIN_ROOT}``
  token via :mod:`scripts.lib.path_rewrite`.
- Each Claude slash command becomes a skill with ``disable-model-invocation:
  true`` so it surfaces as ``/define``, ``/build``, etc. — without the
  ``agentspec:`` namespace.
- Each agent has Claude-only frontmatter fields normalized into a portable
  subset that Cursor understands.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.lib import frontmatter, packaging, platforms
from scripts.lib.packaging import (
    EXTRAS_DIR, REPO_ROOT, SCRIPTS_DIR, SOURCE_DIR,
    BuildSummary, info, ok, warn, fail, print_summary,
)


PROFILE = platforms.get_profile(platforms.CURSOR)
PLUGIN_VERSION = "3.3.0"


# ── Command → Skill conversion ───────────────────────────────────────────────

def _command_to_skill(command_path: Path, skills_dir: Path) -> None:
    """Convert a Claude command markdown file into a Cursor skill.

    The skill keeps the original body verbatim — only frontmatter is
    rewritten. ``disable-model-invocation: true`` ensures the skill only
    runs when the user types ``/<name>`` explicitly.
    """
    fm = frontmatter.parse_file(command_path)
    name = str(fm.data.get("name") or command_path.stem)
    description = str(fm.data.get("description") or f"AgentSpec command: {name}")

    skill_root = skills_dir / name
    skill_root.mkdir(parents=True, exist_ok=True)
    skill_text = frontmatter.render(
        {
            "name": name,
            "description": description.replace("\n", " "),
            "disable-model-invocation": True,
        },
        fm.body if fm.body else command_path.read_text(encoding="utf-8"),
    )
    (skill_root / "SKILL.md").write_text(skill_text, encoding="utf-8")


def _convert_commands(output_dir: Path) -> int:
    """Mirror ``commands/`` and emit skills for the slash command UX."""
    commands_src = output_dir / "commands"
    skills_dir = output_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    if not commands_src.exists():
        return 0
    for md in commands_src.rglob("*.md"):
        if md.name.lower() == "readme.md":
            continue
        _command_to_skill(md, skills_dir)
        count += 1
    return count


# ── Agent frontmatter normalization ──────────────────────────────────────────

# Cursor honors a portable subset. Claude-specific fields stay in the body so
# the prompt still benefits from them, but Cursor does not error on unknown
# frontmatter keys; we simply prune the ones that have no effect there.
_DROP_FIELDS = frozenset({
    "tier", "color", "stop_conditions", "escalation_rules",
    "anti_pattern_refs", "kb_domains",
})


def _normalize_agent(agent_path: Path) -> None:
    """Rewrite an agent file with a Cursor-friendly frontmatter block."""
    fm = frontmatter.parse_file(agent_path)
    if not fm.data:
        return
    portable: dict[str, object] = {}
    for key in ("name", "description", "model", "tools"):
        if key in fm.data:
            portable[key] = fm.data[key]
    # Always carry an explicit name for invocability.
    portable.setdefault("name", agent_path.stem)
    portable.setdefault("description", f"AgentSpec specialist: {agent_path.stem}")
    rendered = frontmatter.render(portable, fm.body)
    agent_path.write_text(rendered, encoding="utf-8")


def _normalize_agents(output_dir: Path) -> int:
    agent_dir = output_dir / "agents"
    if not agent_dir.exists():
        return 0
    count = 0
    for md in agent_dir.rglob("*.md"):
        if md.name in {"README.md", "_template.md"}:
            continue
        _normalize_agent(md)
        count += 1
    return count


# ── Manifest emitters ────────────────────────────────────────────────────────

def _emit_manifest(output_dir: Path) -> None:
    """Emit both Cursor-native and Claude-format manifests for portability."""
    cursor_manifest = {
        "name": "agentspec",
        "version": PLUGIN_VERSION,
        "description": (
            "AgentSpec: Spec-Driven Data Engineering for Cursor — "
            "58 agents, 31 commands, 24 KB domains."
        ),
        "author": {
            "name": "Luan Moreno",
            "email": "luan.moreno@owshq.com",
            "url": "https://github.com/luanmorenommaciel",
        },
        "license": "MIT",
        "repository": "https://github.com/luanmorenommaciel/agentspec",
        "skills": "skills/",
        "agents": "agents/",
        "commands": "commands/",
        "hooks": "hooks/hooks.json",
        "mcpServers": ".mcp.json",
    }
    cursor_dir = output_dir / ".cursor-plugin"
    packaging.write_json(cursor_dir / "plugin.json", cursor_manifest)

    # Claude-format mirror so VS Code or Claude Code can also load this bundle.
    claude_manifest = {
        **cursor_manifest,
        "description": cursor_manifest["description"] + " (Claude-format mirror).",
    }
    packaging.write_json(output_dir / ".claude-plugin" / "plugin.json", claude_manifest)


def _emit_mcp_config(output_dir: Path) -> None:
    """Bundle a stub ``.mcp.json`` pointing at AgentSpec MCP if installed."""
    mcp_config = {
        "mcpServers": {
            "agentspec-mcp": {
                "command": "python3",
                "args": [
                    "${PLUGIN_ROOT}/mcp/server.py",
                ],
                "env": {
                    "AGENTSPEC_ROOT": "${PLUGIN_ROOT}",
                },
            }
        }
    }
    packaging.write_json(output_dir / ".mcp.json", mcp_config)


def _copy_source(output_dir: Path) -> None:
    for sub in ("agents", "commands", "skills", "kb"):
        src = SOURCE_DIR / sub
        if src.exists():
            packaging.copy_source_tree(src, output_dir / sub)
    sdd_target = output_dir / "sdd"
    sdd_target.mkdir(parents=True, exist_ok=True)
    for sub in ("templates", "architecture"):
        s = SOURCE_DIR / "sdd" / sub
        if s.exists():
            packaging.copy_source_tree(s, sdd_target / sub)
    for fname in ("_index.md", "README.md"):
        f = SOURCE_DIR / "sdd" / fname
        if f.exists():
            shutil.copy2(f, sdd_target / fname)


def _copy_extras(output_dir: Path) -> None:
    if not EXTRAS_DIR.exists():
        return
    skill_root = output_dir / "skills"
    skill_root.mkdir(parents=True, exist_ok=True)
    for skill_dir in (EXTRAS_DIR / "skills").iterdir() if (EXTRAS_DIR / "skills").exists() else []:
        if skill_dir.is_dir():
            packaging.copy_source_tree(skill_dir, skill_root / skill_dir.name)
    for sub in ("hooks", "scripts"):
        s = EXTRAS_DIR / sub
        if s.exists():
            packaging.copy_source_tree(s, output_dir / sub)


def _ship_judge(output_dir: Path) -> None:
    judge_src = SCRIPTS_DIR / "judge.py"
    if not judge_src.exists():
        warn("scripts/judge.py missing — /judge will not work in the Cursor pack")
        return
    target = output_dir / "scripts"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(judge_src, target / "judge.py")


def build(strict_stale: bool = True) -> BuildSummary:
    output_dir = platforms.dist_root(REPO_ROOT, PROFILE.id)
    packaging.regenerate_agent_router()
    packaging.clean_output(output_dir)
    _copy_source(output_dir)
    _copy_extras(output_dir)
    _ship_judge(output_dir)
    converted = _convert_commands(output_dir)
    normalized = _normalize_agents(output_dir)
    info(f"Skills generated from commands: {converted}")
    info(f"Agent frontmatter normalized: {normalized}")
    results = packaging.rewrite_paths(output_dir, PROFILE)
    _emit_manifest(output_dir)
    _emit_mcp_config(output_dir)
    summary = packaging.summarize(PROFILE, output_dir, results)
    if strict_stale and summary.stale_findings > 0:
        fail(f"{summary.stale_findings} stale .claude/ references in {output_dir}")
        raise SystemExit(2)
    report = {
        "platform": PROFILE.id,
        "label": PROFILE.label,
        "version": PLUGIN_VERSION,
        "skills": summary.skills,
        "agents": summary.agents,
        "commands": summary.commands,
        "kb_domains": summary.kb_domains,
        "converted_commands": converted,
        "normalized_agents": normalized,
        "rewrite_changes": summary.rewrite_changes,
        "stale_findings": summary.stale_findings,
        "output": str(output_dir),
    }
    packaging.write_json(output_dir / "build-report.json", report)
    print_summary(summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-stale", action="store_true")
    args = parser.parse_args()
    try:
        build(strict_stale=not args.allow_stale)
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
