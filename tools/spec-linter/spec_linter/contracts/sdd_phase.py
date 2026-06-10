"""SDD-phase contract (loaded as data).

Built from a phase's `required_sections` (e.g., from WORKFLOW_CONTRACTS.yaml)
and validates a Markdown document: each required section must be present as a
heading. WHAT is checked (the section list) is data; severity is the contract's
choice (FAIL on a missing required section).
"""

from __future__ import annotations

import re

from ..verdict import Finding, Level

_HEADING = re.compile(r"^#{1,6}\s+(.*\S)\s*$", re.MULTILINE)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


class SddPhaseContract:
    def __init__(self, phase: str, required_sections: list[str]) -> None:
        self.name = f"sdd-phase:{phase}"
        self._required = required_sections

    def parse(self, artifact: str) -> set[str]:
        return {_slug(m.group(1)) for m in _HEADING.finditer(artifact)}

    def check(self, present: set[str]) -> list[Finding]:
        findings: list[Finding] = []
        for section in self._required:
            if _slug(section) not in present:
                findings.append(
                    Finding(
                        level=Level.FAIL,
                        rule="L2.required_section",
                        field=section,
                        message=f"required section '{section}' is missing",
                        expected="section present as a heading",
                        found="absent",
                    )
                )
        return findings
