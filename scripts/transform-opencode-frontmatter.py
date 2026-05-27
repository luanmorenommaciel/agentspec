#!/usr/bin/env python3
"""Transform Claude Code agent frontmatter for OpenCode compatibility.

Reads a source agent .md file (.claude/agents/), extracts the ``tools:``
list, maps each Claude Code tool name to an OpenCode ``permission`` key,
inserts a ``permission:`` block and ``mode: subagent`` into the frontmatter,
and writes the result.

MCP tool patterns (``mcp__*``) are dropped — they have no OpenCode
permission equivalent.

No external dependencies — uses only stdlib regex, same approach as
``generate-agent-router.py``.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# ── Tool name mapping ─────────────────────────────────────────────────────────

_TOOL_TO_PERMISSION: dict[str, str] = {
    "read": "read",
    "write": "edit",
    "edit": "edit",
    "multiedit": "edit",
    "grep": "grep",
    "glob": "glob",
    "bash": "bash",
    "todowrite": "todowrite",
    "askuserquestion": "question",
    "websearch": "websearch",
    "webfetch": "webfetch",
    "task": "task",
}

_MCP_RE = re.compile(r"^mcp__", re.IGNORECASE)
_EXCLUDED_TOOLS_RE = re.compile(r"^(mcp__|askuserquestion)", re.IGNORECASE)

# ── Frontmatter regex (same pattern as generate-agent-router.py) ──────────────

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_TOOLS_RE = re.compile(r"^tools:\s*\[([^\]]*)\]", re.MULTILINE)


def _parse_tools(fm_body: str) -> list[str]:
    """Extract the list of tool names from a ``tools: [...]`` line."""
    m = _TOOLS_RE.search(fm_body)
    if not m:
        return []
    raw = m.group(1)
    items = [s.strip().strip("\"'") for s in raw.split(",") if s.strip()]
    return items


def _tools_to_permissions(tool_names: list[str]) -> set[str]:
    """Map Claude Code tool names to OpenCode permission keys.

    Deduplicates: ``Write`` + ``Edit`` + ``MultiEdit`` all map to ``edit``.
    Strips MCP patterns (``mcp__*``).
    """
    permissions: set[str] = set()
    for name in tool_names:
        key = name.lower()
        if _EXCLUDED_TOOLS_RE.match(key):
            continue
        perm = _TOOL_TO_PERMISSION.get(key)
        if perm:
            permissions.add(perm)
    return permissions


def _build_permission_block(permissions: set[str]) -> str:
    """Generate the ``permission:`` YAML block."""
    lines = ["permission:"]
    for perm in sorted(permissions):
        lines.append(f"  {perm}: allow")
    return "\n".join(lines)


_COLOR_RE = re.compile(r"^color:\s*\S+\s*$", re.MULTILINE)
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def transform(source_text: str) -> str:
    """Transform a .md string: strip Claude-only fields, inject permission + mode.

    Drops ``tools:`` (OpenCode rejects list format) and ``color:`` (OpenCode
    rejects non-standard values). Injects ``permission:`` and ``mode: subagent``
    blocks in their place.

    Returns the transformed text.
    """
    fm_match = _FRONTMATTER_RE.match(source_text)
    if not fm_match:
        return source_text

    fm_body = fm_match.group(1)
    fm_start = fm_match.start()
    fm_end = fm_match.end()

    tools = _parse_tools(fm_body)
    permissions = _tools_to_permissions(tools)
    perm_block = _build_permission_block(permissions)

    # Capture the tools: line position before we strip it
    tools_match = _TOOLS_RE.search(fm_body)
    insert_pos = tools_match.start() if tools_match else 0

    # Strip Claude Code-only fields that break OpenCode
    fm_body = _TOOLS_RE.sub("", fm_body)          # remove tools: [...]
    fm_body = _COLOR_RE.sub("", fm_body)           # remove color: orange etc
    fm_body = _BLANK_LINES_RE.sub("\n\n", fm_body)  # collapse extra blank lines

    new_fm_body = fm_body[:insert_pos].rstrip() + \
        "\n" + perm_block + "\nmode: subagent\n" + \
        fm_body[insert_pos:].lstrip()

    result = source_text[:fm_start] + "---\n" + new_fm_body + "\n---\n" + source_text[fm_end:]
    return result


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <source.md> <dest.md>", file=sys.stderr)
        sys.exit(2)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    if not src.exists():
        print(f"Error: source file not found: {src}", file=sys.stderr)
        sys.exit(1)

    text = src.read_text(encoding="utf-8")
    transformed = transform(text)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(transformed, encoding="utf-8")


if __name__ == "__main__":
    main()
