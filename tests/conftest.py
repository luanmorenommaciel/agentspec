"""Shared pytest setup: make the repo root importable so tests can import scripts/."""
from __future__ import annotations

import sys
from pathlib import Path

# Make `scripts/` importable without requiring a package install step.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"

for path in (_REPO_ROOT, _SCRIPTS_DIR):
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)
