"""The emit boundary: promotion and provenance in one module.

Promotion never renames across filesystems — the staged bytes are copied to a
temporary name INSIDE the emit target's own directory and then renamed over the
target, so the visible transition is atomic whatever volume the run directory
lives on. The rename is made durable by syncing the target's DIRECTORY, not only
the file. On any failure the target is left untouched and the staged copy remains
for inspection. Fail closed.

The archive is provenance, never load-bearing: the spec verbatim plus a
`provenance.json` describing the run. Nothing here is ever read back to operate —
deleting the archive changes no behavior.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from .runstate import now, workspace_root

_DEFAULT_TEMPLATE = ".claude/sdd/archive/specs/{name}/"


class EmitError(OSError):
    """The emit boundary could not complete the step it was asked to perform."""


def promote(staged: Path, target: Path) -> Path:
    if not staged.is_file():
        raise EmitError(f"nothing staged at {staged}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.tmp-{uuid.uuid4().hex[:12]}")
    try:
        with staged.open("rb") as source, temporary.open("wb") as sink:
            shutil.copyfileobj(source, sink)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temporary, target)
        directory = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise EmitError(f"could not promote {staged} to {target}: {exc}") from exc
    return target


def resolve_archive_dir(name: str, template: str | None, workspace: Path | None = None) -> Path:
    """Validate the archive template BEFORE any stage runs: it must be relative,
    and its resolved destination must lie under the workspace root. An invalid
    template is an operational error, never a promoted artifact with no provenance."""
    raw = template or _DEFAULT_TEMPLATE
    if Path(raw).is_absolute():
        raise EmitError(f"archive template must be a relative path, got {raw!r}")
    root = (workspace or workspace_root()).resolve()
    destination = (root / raw.format(name=name)).resolve()
    if not destination.is_relative_to(root):
        raise EmitError(f"archive destination {destination} escapes the workspace root {root}")
    return destination


def archive_spec(destination: Path, spec: Path, provenance: dict[str, Any]) -> Path:
    """Write the spec verbatim plus provenance. The live run log is deliberately
    NOT copied: it belongs to the disposable run directory and is still open.

    The destination is keyed by the artifact NAME, so two artifacts sharing a name
    would resolve to the same archive. Overwriting one build record with another's
    would silently destroy provenance, so a destination already describing a
    DIFFERENT target is refused rather than replaced."""
    existing = destination / "provenance.json"
    if existing.is_file():
        try:
            recorded = json.loads(existing.read_text(encoding="utf-8")).get("target")
        except (OSError, ValueError):
            recorded = None
        if recorded is not None and recorded != provenance.get("target"):
            raise EmitError(
                f"{existing} already holds provenance for {recorded}; "
                "artifact names must be unique across the archive"
            )
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(spec, destination / spec.name)
    (destination / "provenance.json").write_text(
        json.dumps({**provenance, "archived_at": now()}, indent=2) + "\n", encoding="utf-8"
    )
    return destination
