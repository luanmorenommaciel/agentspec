"""Generation bindings — the shipped handoff and its offline fake.

A deterministic process cannot invoke a host sub-agent in-process, so the shipped
binding does not generate: it reports whether the expected output exists for the
current attempt and lets the conductor pause. ONE seam serves both producing
kinds, so spec creation and artifact generation are the same handoff and the
shared budget can be driven across both edges in-process by a fake. The host
session is the outer loop; the conductor is the inner deterministic step; the
seam between them is a file plus an exit code.
"""

from __future__ import annotations

import os
from collections.abc import Callable

from .models import GenerationOutcome, GenerationRequest


class StagedArtifactGenerator:
    name = "staged-artifact"

    def generate(self, request: GenerationRequest) -> GenerationOutcome:
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        if request.output_path.is_file():
            return GenerationOutcome(produced=True, path=request.output_path)
        noun = "spec" if request.kind == "create" else "artifact"
        return GenerationOutcome(
            produced=False,
            path=request.output_path,
            detail=(
                f"write the {noun} for attempt {request.attempt} to this path, "
                "then re-run the identical command"
            ),
        )


class FakeGenerator:
    """Deterministic generator for tests: a `(request) -> str | None` script whose
    return value is written to the expected output path. Returning None reports
    "not produced", exercising the waiting handoff with no I/O of the caller's own.
    Because the same seam serves `create` and `generate`, one script can drive both
    feedback edges."""

    name = "fake"

    def __init__(self, script: Callable[[GenerationRequest], str | None]) -> None:
        self._script = script

    def generate(self, request: GenerationRequest) -> GenerationOutcome:
        body = self._script(request)
        if body is None:
            return GenerationOutcome(produced=False, path=request.output_path)
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = request.output_path.with_name(request.output_path.name + ".tmp")
        temporary.write_text(body, encoding="utf-8")
        os.replace(temporary, request.output_path)
        return GenerationOutcome(produced=True, path=request.output_path)
