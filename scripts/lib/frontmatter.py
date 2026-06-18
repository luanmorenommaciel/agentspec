"""Minimal YAML-ish frontmatter parsing shared across the build core.

Author: Emerson Antonio
Date: 2026-06-17

We deliberately avoid a full YAML dependency so the build core remains
zero-install. The agent frontmatter in ``.claude/agents/`` is line-based
and well-formed; this module covers the keys we actually need for the
multi-platform adapters.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass(frozen=True, slots=True)
class Frontmatter:
    """Parsed view of a markdown frontmatter block."""

    raw: str                              # original frontmatter body
    body: str                             # markdown body after frontmatter
    data: dict[str, object]               # extracted scalar/list fields


def split(text: str) -> tuple[str, str]:
    """Return ``(frontmatter_block, body)`` or ``("", text)`` if absent."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return "", text
    block = match.group(1)
    body = text[match.end():]
    return block, body


def parse(text: str) -> Frontmatter:
    """Parse the first frontmatter block in ``text``.

    Supported keys: ``name``, ``description`` (scalar or block), ``tier``,
    ``model``, ``color``, ``kb_domains`` (inline list), ``tools`` (inline list),
    ``escalation_rules`` (list of objects with ``target`` field).
    """
    block, body = split(text)
    if not block:
        return Frontmatter(raw="", body=text, data={})

    data: dict[str, object] = {}

    # Scalar keys
    for key in ("name", "tier", "model", "color"):
        m = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
        if m:
            data[key] = m.group(1).strip().strip("'\"")

    # description: block scalar OR single line
    m = re.search(r"^description:\s*\|\s*\n((?:[ \t]+.*\n?)+)", block, re.MULTILINE)
    if m:
        # Preserve indentation removal so consumers get clean text
        lines = m.group(1).splitlines()
        if lines:
            indent = len(lines[0]) - len(lines[0].lstrip())
            data["description"] = "\n".join(line[indent:] if len(line) >= indent else line for line in lines).strip()
    else:
        m = re.search(r"^description:\s*(.+)$", block, re.MULTILINE)
        if m:
            data["description"] = m.group(1).strip()

    # kb_domains: [a, b, c]
    m = re.search(r"^kb_domains:\s*\[([^\]]*)\]", block, re.MULTILINE)
    if m:
        items = [s.strip().strip("'\"") for s in m.group(1).split(",") if s.strip()]
        data["kb_domains"] = items

    # tools: [Read, Write, ...]
    m = re.search(r"^tools:\s*\[([^\]]*)\]", block, re.MULTILINE)
    if m:
        items = [s.strip() for s in m.group(1).split(",") if s.strip()]
        data["tools"] = items

    # escalation_rules — extract target identifiers
    targets: list[str] = []
    in_block = False
    for line in block.splitlines():
        if re.match(r"^escalation_rules:\s*$", line):
            in_block = True
            continue
        if in_block:
            if line and not line.startswith(" ") and not line.startswith("-"):
                in_block = False
                continue
            m = re.match(r"\s*target:\s*['\"]?([a-z0-9\-]+)['\"]?\s*$", line)
            if m:
                targets.append(m.group(1))
    if targets:
        data["escalation_rules"] = targets

    return Frontmatter(raw=block, body=body, data=data)


def parse_file(path: Path) -> Frontmatter:
    """Read ``path`` and parse its frontmatter."""
    return parse(path.read_text(encoding="utf-8"))


def render(data: dict[str, object], body: str) -> str:
    """Render a portable frontmatter block + body.

    Used by the Cursor and Copilot adapters to emit normalized files. Only
    simple scalar/list values are supported; nested objects must be passed
    as pre-rendered strings.
    """
    if not data:
        return body

    lines = ["---"]
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        elif isinstance(value, (list, tuple)):
            if all(isinstance(item, str) and "," not in item and "'" not in item for item in value):
                rendered = ", ".join(value)
                lines.append(f"{key}: [{rendered}]")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
        elif isinstance(value, str):
            if "\n" in value:
                lines.append(f"{key}: |")
                for sub in value.splitlines():
                    lines.append(f"  {sub}")
            else:
                lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + body
