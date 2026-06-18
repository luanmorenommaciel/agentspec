"""Shared build core for AgentSpec multi-platform distribution.

Modules:
- platforms: target profiles (claude, cursor, vscode-copilot, mcp)
- path_rewrite: deterministic path token substitution per platform
- frontmatter: shared YAML-ish frontmatter parser (mirrors generate-agent-router)
- packaging: copy + transform helpers shared by per-platform builders
"""

__all__ = ["platforms", "path_rewrite", "frontmatter", "packaging"]
