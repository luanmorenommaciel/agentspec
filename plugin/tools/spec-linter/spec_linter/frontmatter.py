"""Frontmatter extraction — the leading ``---``-fenced YAML block of a
self-contained Markdown artifact (e.g. an agent's `.md` file, where the
frontmatter IS the spec).
"""

from __future__ import annotations

import re
from typing import Any

import yaml

_FENCE = re.compile(r"(?m)^---\s*$")


class FrontmatterError(ValueError):
    """A ``---`` block is present but is not valid YAML, or not a mapping."""


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Split a leading ``---``-fenced YAML block from the rest of `text`.

    Mirrors spec-judge's parsing behavior: splits only on a standalone fence
    line (``---`` alone on its line, at column 0), so a YAML block scalar
    (e.g. ``description: |``) may contain an indented line that merely looks
    like an hrule without it being mistaken for the closing fence, and an
    hrule in the body *after* the real closing fence is left untouched.

    Returns ``(None, text)`` when no frontmatter block is structurally
    present — the text does not open with a standalone ``---`` fence, or no
    closing fence follows. That is the ordinary "no spec attached" case.

    Diverges from spec-judge once an opening AND closing fence are both
    present: if the enclosed YAML fails to parse, or parses to something
    other than a mapping, raises `FrontmatterError` instead of silently
    falling back to ``(None, text)``. A present-but-broken block must surface
    loudly, not read as "no frontmatter".
    """
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return None, text
    parts = _FENCE.split(stripped, maxsplit=2)
    if len(parts) < 3:
        return None, text
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"frontmatter is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise FrontmatterError(f"frontmatter must be a YAML mapping, got {type(data).__name__}")
    return data, parts[2].lstrip("\n")
