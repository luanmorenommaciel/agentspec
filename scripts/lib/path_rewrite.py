"""Path rewriting for the AgentSpec multi-target build.

Author: Emerson Antonio
Date: 2026-06-17

Replaces references to the canonical ``.claude/`` source layout with the
platform-specific root token while preserving workspace output paths
(``.claude/sdd/features`` and friends) that point to the user's project.

The rewriter is intentionally regex-based: we are not parsing markdown,
we are normalizing references that humans wrote as relative paths so that
shipped artifacts can be loaded by Claude Code, Cursor or VS Code+Copilot
without modification.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .platforms import PlatformProfile


# ── Configuration ────────────────────────────────────────────────────────────

# Directories under ``.claude/`` that map to platform plugin paths.
# Order matters: longer prefixes first so we never replace a substring of a
# longer match.
_PLUGIN_DIRS: tuple[str, ...] = (
    "sdd/templates",
    "sdd/architecture",
    "agents",
    "commands",
    "skills",
    "kb",
)

# Single-file refs that must be rewritten even when they are not under one of
# the directory roots above.
_PLUGIN_FILES: tuple[str, ...] = (
    "sdd/_index.md",
    "sdd/README.md",
)

# Workspace paths must be preserved verbatim — Claude Code, Cursor and
# Copilot all execute hooks from the user's project, so these stay relative.
# Any prefix here marks a reference as intentional in the shipped artifact.
_WORKSPACE_PATHS: tuple[str, ...] = (
    ".claude/sdd",               # user feature/report/archive outputs
    ".claude/storage",           # judge ledger and similar local state
    ".claude/settings",
    ".claude/plans",
    ".claude/memory",
    ".claude/CLAUDE.md",         # user's project conventions file
    ".claude/agents/workflow",   # init-workspace creates this in the user repo
    ".claude/agents/custom",     # init-workspace creates this in the user repo
)


# Files we rewrite — markdown, YAML, JSON, plus shell/Python that may
# reference the source layout.
TEXT_SUFFIXES: frozenset[str] = frozenset({
    ".md", ".yaml", ".yml", ".json", ".sh", ".py",
})


# ── Public surface ───────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RewriteResult:
    """Outcome of a single-file rewrite. Useful for tests and reporting."""

    path: Path
    changed: bool
    bytes_before: int
    bytes_after: int


# Legacy token used in handcrafted artifacts (hooks/hooks.json, helper scripts)
# that were authored against the Claude Code variable. Non-Claude targets must
# migrate it to their own root token; Claude keeps it verbatim.
LEGACY_ROOT_TOKEN: str = "${CLAUDE_PLUGIN_ROOT}"


def rewrite_text(text: str, profile: PlatformProfile) -> str:
    """Apply the canonical ``.claude/`` → ``{root_token}`` rewrite.

    The function is pure: same input + profile produce the same output.
    It does not protect workspace paths because the regex below only matches
    the plugin-internal prefixes — anything outside that set is left alone.

    When the target profile uses a root token other than the legacy
    ``${CLAUDE_PLUGIN_ROOT}``, every literal occurrence of that legacy token
    is migrated to the target token. This is required for shipped artifacts
    like ``hooks/hooks.json`` that hardcode the Claude variable.
    """
    if not text:
        return text

    out = text
    token = profile.root_token

    # Directory roots: .claude/<dir>/ → {token}/<dir>/
    for plugin_dir in _PLUGIN_DIRS:
        pattern = re.compile(rf"\.claude/{re.escape(plugin_dir)}/")
        out = pattern.sub(f"{token}/{plugin_dir}/", out)

    # Single-file refs: .claude/sdd/_index.md → {token}/sdd/_index.md
    for plugin_file in _PLUGIN_FILES:
        pattern = re.compile(rf"\.claude/{re.escape(plugin_file)}")
        out = pattern.sub(f"{token}/{plugin_file}", out)

    # Legacy token migration: ${CLAUDE_PLUGIN_ROOT} → {target token} for
    # non-Claude targets. Avoids a no-op self-replacement on the Claude target.
    if token != LEGACY_ROOT_TOKEN:
        out = out.replace(LEGACY_ROOT_TOKEN, token)

    # Absolute paths that include the canonical root and survived earlier
    # transforms — strip the leading filesystem prefix so they look like
    # tokens. Example: /Users/x/agentspec/${ROOT}/skills/... → ${ROOT}/skills/...
    escaped_token = re.escape(token)
    out = re.sub(
        rf"/[^\s\"'`]*{escaped_token}/",
        f"{token}/",
        out,
    )

    return out


def rewrite_file(path: Path, profile: PlatformProfile) -> RewriteResult:
    """Rewrite a single text file in place. Returns a result object."""
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Binary or non-UTF-8 file — skip silently. The builder excludes most
        # of these via TEXT_SUFFIXES but we double-check here.
        return RewriteResult(path=path, changed=False, bytes_before=0, bytes_after=0)

    updated = rewrite_text(original, profile)
    if updated == original:
        return RewriteResult(
            path=path, changed=False,
            bytes_before=len(original.encode("utf-8")),
            bytes_after=len(original.encode("utf-8")),
        )

    path.write_text(updated, encoding="utf-8")
    return RewriteResult(
        path=path,
        changed=True,
        bytes_before=len(original.encode("utf-8")),
        bytes_after=len(updated.encode("utf-8")),
    )


def rewrite_tree(root: Path, profile: PlatformProfile, suffixes: Iterable[str] = TEXT_SUFFIXES) -> list[RewriteResult]:
    """Walk ``root`` and rewrite every text file with a known suffix."""
    suffix_set = frozenset(suffixes)
    results: list[RewriteResult] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in suffix_set:
            continue
        # Never rewrite the manifest itself; the build emits manifests as
        # structured JSON instead of patching them with sed.
        if ".claude-plugin" in path.parts or ".cursor-plugin" in path.parts:
            continue
        results.append(rewrite_file(path, profile))
    return results


def stale_references(root: Path, profile: PlatformProfile) -> list[tuple[Path, int, str]]:
    """Return a list of stale ``.claude/`` references in the built tree.

    We exclude workspace paths because those are intentional. Anything else
    in the output is considered stale and the build should fail.
    """
    findings: list[tuple[Path, int, str]] = []
    workspace_set = set(_WORKSPACE_PATHS)

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if ".claude-plugin" in path.parts or ".cursor-plugin" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if ".claude/" not in line:
                continue
            # Skip pure comment lines (shell, python, yaml) — they describe
            # workspace behavior, not plugin references.
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            # Skip lines that only reference intentional workspace paths
            if any(ws in line for ws in workspace_set):
                continue
            # Skip lines already migrated to the platform token
            if profile.root_token in line:
                continue
            findings.append((path, i, line.rstrip()))
    return findings
