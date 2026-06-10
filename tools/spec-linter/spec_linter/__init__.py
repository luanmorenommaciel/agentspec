"""Spec Linter — Gate A (spec validity) prototype for AgentSpec."""

from .linter import emit_json_schema, lint_dir, lint_file, lint_spec
from .models import AgentSpec
from .verdict import Finding, Level, Verdict

__all__ = [
    "AgentSpec",
    "Finding",
    "Level",
    "Verdict",
    "emit_json_schema",
    "lint_dir",
    "lint_file",
    "lint_spec",
]
