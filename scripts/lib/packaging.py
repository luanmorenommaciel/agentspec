"""Shared packaging helpers for AgentSpec multi-target builds.

Author: Emerson Antonio
Date: 2026-06-17

Each per-platform builder calls into these helpers so we avoid scattering
copy/clean/rewrite logic across multiple scripts.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .path_rewrite import RewriteResult, rewrite_tree, stale_references
from .platforms import PlatformProfile


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_DIR = REPO_ROOT / ".claude"
EXTRAS_DIR = REPO_ROOT / "plugin-extras"
SCRIPTS_DIR = REPO_ROOT / "scripts"


# ── Logging helpers ──────────────────────────────────────────────────────────

class _Color:
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"


def info(msg: str) -> None:
    print(f"{_Color.BLUE}[INFO]{_Color.NC} {msg}")


def ok(msg: str) -> None:
    print(f"{_Color.GREEN}[OK]{_Color.NC} {msg}")


def warn(msg: str) -> None:
    print(f"{_Color.YELLOW}[WARN]{_Color.NC} {msg}")


def fail(msg: str) -> None:
    print(f"{_Color.RED}[ERROR]{_Color.NC} {msg}", file=sys.stderr)


# ── Counts and summary ───────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class BuildSummary:
    """Counts the build produced. Drives validate-dist.py and CI."""

    profile_id: str
    output_dir: Path
    agents: int
    commands: int
    skills: int
    kb_domains: int
    rewrite_changes: int
    stale_findings: int


def summarize(profile: PlatformProfile, output_dir: Path, results: Iterable[RewriteResult]) -> BuildSummary:
    """Count artifacts in the produced tree."""
    agent_dir = output_dir / profile.agent_root
    command_dir = output_dir / profile.command_root
    skill_dir = output_dir / profile.skill_root
    kb_dir = output_dir / profile.kb_root

    def _count_md(root: Path, exclude: set[str]) -> int:
        if not root.exists():
            return 0
        return sum(1 for p in root.rglob("*.md") if p.name not in exclude)

    def _count_skills(root: Path) -> int:
        if not root.exists():
            return 0
        return sum(1 for p in root.rglob("SKILL.md"))

    def _count_kb(root: Path) -> int:
        if not root.exists():
            return 0
        return sum(
            1 for child in root.iterdir()
            if child.is_dir() and child.name not in {"_templates"}
        )

    changes = sum(1 for r in results if r.changed)
    stales = stale_references(output_dir, profile)

    return BuildSummary(
        profile_id=profile.id,
        output_dir=output_dir,
        agents=_count_md(agent_dir, exclude={"README.md", "_template.md"}),
        commands=_count_md(command_dir, exclude={"README.md"}),
        skills=_count_skills(skill_dir),
        kb_domains=_count_kb(kb_dir),
        rewrite_changes=changes,
        stale_findings=len(stales),
    )


def print_summary(summary: BuildSummary) -> None:
    print("")
    print("=" * 60)
    ok(f"Build complete: {summary.profile_id}")
    print("=" * 60)
    print(f"  Output:        {summary.output_dir}")
    print(f"  Agents:        {summary.agents}")
    print(f"  Commands:      {summary.commands}")
    print(f"  Skills:        {summary.skills}")
    print(f"  KB domains:    {summary.kb_domains}")
    print(f"  Rewrites:      {summary.rewrite_changes}")
    print(f"  Stale paths:   {summary.stale_findings}")
    print("=" * 60)


# ── Filesystem helpers ───────────────────────────────────────────────────────

def clean_output(output_dir: Path) -> None:
    """Wipe an existing build directory but keep the parent ``dist/``."""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


_IGNORE_PATTERNS = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", ".DS_Store", ".pytest_cache",
)


def copy_source_tree(source: Path, destination: Path) -> None:
    """Copy a source tree, replacing any existing destination tree."""
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, symlinks=False, ignore=_IGNORE_PATTERNS)


def copy_if_exists(source: Path, destination: Path) -> bool:
    """Best-effort file copy. Returns ``True`` if the source existed."""
    if not source.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        copy_source_tree(source, destination)
    else:
        shutil.copy2(source, destination)
    return True


def remove_workspace_dirs(plugin_dir: Path) -> None:
    """Drop user-workspace directories that must never ship with a plugin."""
    for relative in ("sdd/features", "sdd/reports", "sdd/archive"):
        target = plugin_dir / relative
        if target.exists():
            shutil.rmtree(target)


# ── Agent router regeneration ────────────────────────────────────────────────

def regenerate_agent_router(check_only: bool = False) -> None:
    """Re-run the agent-router generator so the shipped SKILL.md is fresh."""
    generator = SCRIPTS_DIR / "generate-agent-router.py"
    if not generator.exists():
        warn("scripts/generate-agent-router.py not found — skipping")
        return
    args = [sys.executable, str(generator)]
    if check_only:
        args.append("--check")
    info("Regenerating agent-router…")
    result = subprocess.run(args, cwd=REPO_ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"agent-router generation failed (exit {result.returncode})")
    ok("agent-router regenerated")


# ── Path rewriting wrapper ───────────────────────────────────────────────────

def rewrite_paths(output_dir: Path, profile: PlatformProfile) -> list[RewriteResult]:
    info(f"Rewriting paths for {profile.id} → {profile.root_token}")
    results = rewrite_tree(output_dir, profile)
    ok(f"Rewrites applied: {sum(1 for r in results if r.changed)}")
    return results


# ── Manifest emitters ────────────────────────────────────────────────────────

def write_json(path: Path, data: object) -> None:
    """Write JSON with stable formatting (sorted keys disabled to keep order)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
