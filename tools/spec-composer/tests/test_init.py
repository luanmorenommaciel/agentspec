"""Tests for the package's import boundary and its public surface."""

from __future__ import annotations

import os
import subprocess
import sys

from conftest import TOOL_ROOT

import spec_composer

_LINTER_ROOT = TOOL_ROOT.parent / "spec-linter"
_JUDGE_ROOT = TOOL_ROOT.parent / "spec-judge"

_PROBE = """
import sys
import spec_composer
assert "spec_judge" not in sys.modules
assert "spec_linter" in sys.modules
spec_composer.compose
spec_composer.judge_artifact
try:
    spec_composer.does_not_exist
except AttributeError:
    pass
else:
    raise SystemExit("expected AttributeError for an unknown attribute")
"""


def test_import_does_not_touch_siblings() -> None:
    pythonpath = os.pathsep.join(str(root) for root in (TOOL_ROOT, _LINTER_ROOT, _JUDGE_ROOT))
    result = subprocess.run(
        [sys.executable, "-c", _PROBE],
        env={**os.environ, "PYTHONPATH": pythonpath},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_public_exports() -> None:
    exports = list(spec_composer.__all__)
    for name in exports:
        assert hasattr(spec_composer, name)

    constants = [name for name in exports if name.isupper()]
    rest = [name for name in exports if not name.isupper()]
    classes = [name for name in rest if name[0].isupper()]
    functions = [name for name in rest if not name[0].isupper()]

    assert exports == constants + classes + functions
    assert constants == sorted(constants)
    assert classes == sorted(classes)
    assert functions == sorted(functions)

    assert "compose" not in exports
    assert "judge_artifact" not in exports
    assert callable(spec_composer.compose)
    assert callable(spec_composer.judge_artifact)
