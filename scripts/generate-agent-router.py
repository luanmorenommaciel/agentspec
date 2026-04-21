#!/usr/bin/env python3
"""Generate the agent-router SKILL.md and routing.json from agent frontmatter.

Single source of truth: each agent's frontmatter under .claude/agents/.
Outputs are deterministic so builds are reproducible and diff-friendly.

Signals derived per agent:
  - name, description (one-liner), tier, model, kb_domains
  - category (from directory: architect/cloud/data-engineering/dev/platform/python/test/workflow)
  - escalations (from escalation_rules.target when present)

Outputs:
  .claude/skills/agent-router/SKILL.md     # Human-readable routing rules
  .claude/skills/agent-router/routing.json # Machine-readable lookup table

Run:
  python3 scripts/generate-agent-router.py
  python3 scripts/generate-agent-router.py --check   # fail if outputs drift
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "agent-router"
SKILL_MD = SKILL_DIR / "SKILL.md"
ROUTING_JSON = SKILL_DIR / "routing.json"

# Skip these filenames in the agents tree
SKIP_FILES: frozenset[str] = frozenset({"README.md", "_template.md"})

# Category label + description per directory
CATEGORIES = {
    "architect":        ("Architecture & Design",       "System-level design, schemas, pipelines, lakehouse"),
    "cloud":            ("Cloud & Infrastructure",      "AWS, GCP, CI/CD, deployment"),
    "data-engineering": ("Data Engineering",            "dbt, Spark, SQL, Airflow, streaming, data quality"),
    "dev":              ("Developer Tools",             "Codebase exploration, meeting analysis, shell, prompts"),
    "platform":         ("Microsoft Fabric",            "Fabric lakehouse, pipelines, AI, security"),
    "python":           ("Python & Code Quality",       "Python dev, review, cleanup, documentation, LLM prompts"),
    "test":             ("Testing & Contracts",         "pytest, data quality, ODCS contracts"),
    "workflow":         ("SDD Workflow",                "Brainstorm, Define, Design, Build, Ship, Iterate"),
}


@dataclass(frozen=True, slots=True)
class AgentSpec:
    """Parsed, normalized view of one agent frontmatter.

    Frozen + slots — AgentSpecs are pure value objects: we build them once
    from disk, serialize them to JSON, and never mutate. Frozen guards that
    invariant; slots eliminates the per-instance ``__dict__`` overhead.
    """

    name: str
    category: str
    path: str
    tier: str
    model: str
    description: str              # first meaningful line of description
    kb_domains: tuple[str, ...] = ()
    escalates_to: tuple[str, ...] = ()


# ── Frontmatter parsing ──────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, object]:
    """Extract the YAML-ish frontmatter block as raw text + a few fields.

    Full YAML parsing would pull a dependency; we only need a handful of keys
    and our frontmatter is well-formed enough for line-based extraction.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    body = match.group(1)

    fm: dict = {"_raw": body}

    # Simple scalar keys
    for key in ("name", "tier", "model", "color"):
        m = re.search(rf"^{key}:\s*(.+)$", body, re.MULTILINE)
        if m:
            fm[key] = m.group(1).strip()

    # description (block scalar `|`)
    m = re.search(r"^description:\s*\|\s*\n((?:[ \t]+.*\n?)+)", body, re.MULTILINE)
    if m:
        fm["description"] = m.group(1)
    else:
        # Single-line description fallback
        m = re.search(r"^description:\s*(.+)$", body, re.MULTILINE)
        if m:
            fm["description"] = m.group(1).strip()

    # kb_domains: [a, b, c] — allow empty list []
    m = re.search(r"^kb_domains:\s*\[([^\]]*)\]", body, re.MULTILINE)
    if m:
        items = [s.strip() for s in m.group(1).split(",") if s.strip()]
        fm["kb_domains"] = items

    # escalation_rules — extract any `target:` values
    escalations: list[str] = []
    in_block = False
    for line in body.splitlines():
        if re.match(r"^escalation_rules:\s*$", line):
            in_block = True
            continue
        if in_block:
            if line and not line.startswith(" ") and not line.startswith("-"):
                in_block = False
                continue
            m = re.match(r"\s*target:\s*['\"]?([a-z0-9\-]+)['\"]?\s*$", line)
            if m:
                escalations.append(m.group(1))
    fm["escalates_to"] = escalations

    return fm


def extract_one_liner(description: str) -> str:
    """Pull the first meaningful sentence out of a description block.

    Skips blank lines, indentation, and example-block markers.
    """
    for raw in description.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("<example>", "</example>", "Example", "**Example", "-", "Context", "user:", "assistant:")):
            break
        return line
    return description.strip().splitlines()[0].strip() if description.strip() else ""


# ── Agent discovery ──────────────────────────────────────────────────────────

def discover_agents() -> list[AgentSpec]:
    """Walk .claude/agents/, parse each agent, return normalized specs."""
    specs: list[AgentSpec] = []
    for md in sorted(AGENTS_DIR.rglob("*.md")):
        if md.name in SKIP_FILES:
            continue
        rel = md.relative_to(REPO_ROOT)
        parts = md.relative_to(AGENTS_DIR).parts
        if len(parts) < 2:
            continue  # Not in a category directory
        category = parts[0]

        text = md.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if not fm or "name" not in fm:
            print(f"[WARN] Skipping {rel} — no parseable frontmatter", file=sys.stderr)
            continue

        specs.append(AgentSpec(
            name=str(fm["name"]),
            category=category,
            path=str(rel),
            tier=str(fm.get("tier", "T1")),
            model=str(fm.get("model", "sonnet")),
            description=extract_one_liner(str(fm.get("description", ""))),
            kb_domains=tuple(fm.get("kb_domains", []) or []),   # pyright: ignore[reportArgumentType]
            escalates_to=tuple(fm.get("escalates_to", []) or []),  # pyright: ignore[reportArgumentType]
        ))
    return specs


# ── Rendering ────────────────────────────────────────────────────────────────

HEADER = """---
name: agent-router
description: Intelligent agent routing -- automatically matches tasks to the best specialist agent based on file patterns, intent keywords, and domain context. Loaded every session to give Claude explicit routing rules for all {agent_count} AgentSpec agents.
---

<!-- =========================================================================
     GENERATED FILE — DO NOT EDIT BY HAND
     Source of truth: .claude/agents/**/*.md frontmatter
     Regenerate:      python3 scripts/generate-agent-router.py
     CI check:        python3 scripts/generate-agent-router.py --check
     ========================================================================= -->

# Agent Router

Explicit routing rules for matching tasks to the correct specialist agent. Generated from each agent's frontmatter, so any change to an agent's `description`, `kb_domains`, or `escalation_rules` flows here automatically.

**Agent count:** {agent_count}  |  **Categories:** {category_count}  |  **Content hash:** `{content_hash}`

"""


def render_category_section(specs: list[AgentSpec]) -> str:
    """One table per agent category."""
    by_category: dict[str, list[AgentSpec]] = {}
    for s in specs:
        by_category.setdefault(s.category, []).append(s)

    out = ["## A. Agents by Category\n"]
    for cat_key, (label, blurb) in CATEGORIES.items():
        group = sorted(by_category.get(cat_key, []), key=lambda s: s.name)
        if not group:
            continue
        out.append(f"### {label}")
        out.append(f"*{blurb}*\n")
        out.append("| Agent | Tier | Model | KB Domains | Escalates To |")
        out.append("|-------|------|-------|-----------|--------------|")
        for s in group:
            kb = ", ".join(f"`{d}`" for d in s.kb_domains) if s.kb_domains else "—"
            esc = ", ".join(f"`{e}`" for e in s.escalates_to) if s.escalates_to else "—"
            out.append(f"| `{s.name}` | {s.tier} | {s.model} | {kb} | {esc} |")
        out.append("")
    return "\n".join(out) + "\n"


def render_kb_index(specs: list[AgentSpec]) -> str:
    """Reverse index: KB domain → agents that use it."""
    index: dict[str, list[str]] = {}
    for s in specs:
        for d in s.kb_domains:
            index.setdefault(d, []).append(s.name)

    out = ["## B. KB Domain → Agents\n"]
    out.append("Which agents know which domain. Use this when the user names a technology.\n")
    out.append("| KB Domain | Agents |")
    out.append("|-----------|--------|")
    for domain in sorted(index):
        agents = ", ".join(f"`{a}`" for a in sorted(index[domain]))
        out.append(f"| `{domain}` | {agents} |")
    return "\n".join(out) + "\n"


def render_one_liners(specs: list[AgentSpec]) -> str:
    """Flat list: agent name + one-line purpose. Useful for semantic matching."""
    out = ["## C. Agent One-Liners\n"]
    out.append("Single-sentence purpose per agent, derived from frontmatter `description`.\n")
    for s in sorted(specs, key=lambda s: s.name):
        out.append(f"- **`{s.name}`** — {s.description}")
    return "\n".join(out) + "\n"


STATIC_FOOTER = """
## D. Model Routing Strategy

Cost-optimize by matching task complexity to model capability.

| Model | Share | Use For |
|-------|-------|---------|
| Haiku | ~70% | File exploration, pattern matching, documentation lookup, simple code generation |
| Sonnet | ~20% | Code review, feature implementation, refactoring, API development, most T1/T2 agents |
| Opus | ~10% | Architectural decisions, complex system design, security reviews, T3 agents |

**Override rules:**
- Agent frontmatter `model:` wins over task-complexity heuristics.
- Tasks touching production data or security escalate to Opus.
- Confidence below 0.75 on Sonnet → retry on Opus before asking user.

## E. Composition Hints

**Parallel** (independent work, different files):
- `dbt-specialist` + `test-generator`
- `code-reviewer` + `data-quality-analyst`
- `schema-designer` + `pipeline-architect`

**Serial** (output feeds next step):
- `schema-designer` → `dbt-specialist`
- `pipeline-architect` → `airflow-specialist`
- `define-agent` → `design-agent` → `build-agent`

**Background** (non-blocking):
- `codebase-explorer`, `code-documenter`, `kb-architect`

## F. How Routing Works

1. **File-pattern signal** — agent's `kb_domains` implies file types (e.g., `dbt` → `models/**/*.sql`).
2. **Intent signal** — the one-liner in `description` is the semantic anchor.
3. **Context signal** — agent's `category` scopes the match to the right domain.
4. **Escalation signal** — `escalation_rules.target` provides the handoff graph.

To change routing, edit the **agent's frontmatter**, not this file. Then run:

```bash
python3 scripts/generate-agent-router.py
```
"""


def render_skill_md(specs: list[AgentSpec], content_hash: str) -> str:
    header = HEADER.format(
        agent_count=len(specs),
        category_count=len({s.category for s in specs}),
        content_hash=content_hash,
    )
    return header + render_category_section(specs) + render_kb_index(specs) + render_one_liners(specs) + STATIC_FOOTER


def render_routing_json(specs: list[AgentSpec]) -> str:
    payload = {
        "version": 1,
        "agent_count": len(specs),
        "agents": [asdict(s) for s in sorted(specs, key=lambda s: s.name)],
        "categories": {k: {"label": v[0], "description": v[1]} for k, v in CATEGORIES.items()},
    }
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def content_hash_for(specs: list[AgentSpec]) -> str:
    """Stable hash over the agent specs — used to detect drift."""
    stable = json.dumps([asdict(s) for s in sorted(specs, key=lambda s: s.name)], sort_keys=True)
    return hashlib.sha256(stable.encode()).hexdigest()[:12]


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate agent-router SKILL.md and routing.json")
    parser.add_argument("--check", action="store_true", help="Fail if generated output differs from on-disk files")
    args = parser.parse_args()

    specs = discover_agents()
    if not specs:
        print("[ERROR] No agents discovered under .claude/agents/", file=sys.stderr)
        return 2

    chash = content_hash_for(specs)
    skill_md = render_skill_md(specs, chash)
    routing_json = render_routing_json(specs)

    if args.check:
        drift = False
        for path, content in [(SKILL_MD, skill_md), (ROUTING_JSON, routing_json)]:
            on_disk = path.read_text(encoding="utf-8") if path.exists() else ""
            if on_disk != content:
                drift = True
                print(f"[DRIFT] {path.relative_to(REPO_ROOT)} is out of date", file=sys.stderr)
                diff = difflib.unified_diff(
                    on_disk.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=f"{path.name} (on disk)",
                    tofile=f"{path.name} (generated)",
                    n=2,
                )
                sys.stderr.writelines(list(diff)[:30])
        if drift:
            print("\n[FAIL] Run: python3 scripts/generate-agent-router.py", file=sys.stderr)
            return 1
        print(f"[OK] agent-router is up to date ({len(specs)} agents, hash {chash})")
        return 0

    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    SKILL_MD.write_text(skill_md, encoding="utf-8")
    ROUTING_JSON.write_text(routing_json, encoding="utf-8")
    print(f"[OK] Wrote {SKILL_MD.relative_to(REPO_ROOT)} and {ROUTING_JSON.relative_to(REPO_ROOT)}")
    print(f"     {len(specs)} agents, {len({s.category for s in specs})} categories, hash {chash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
