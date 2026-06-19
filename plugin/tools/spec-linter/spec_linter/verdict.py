"""Verdict model — the structured, human-readable result of a lint run."""

from __future__ import annotations

from enum import IntEnum

from pydantic import BaseModel, ConfigDict


class Level(IntEnum):
    """Severity, ordered so `max()` picks the worst: FAIL > WARN > PASS."""

    PASS = 0
    WARN = 1
    FAIL = 2

    def __str__(self) -> str:
        return self.name


class Finding(BaseModel):
    model_config = ConfigDict(frozen=True)

    level: Level
    rule: str
    message: str
    field: str | None = None
    expected: str | None = None
    found: str | None = None

    def render(self) -> str:
        loc = f" [{self.field}]" if self.field else ""
        line = f"  {self.level.name:<4} {self.rule}{loc}: {self.message}"
        if self.expected is not None or self.found is not None:
            line += f"\n         expected={self.expected!r} found={self.found!r}"
        return line


class Verdict(BaseModel):
    model_config = ConfigDict(frozen=True)

    level: Level
    findings: list[Finding]

    @classmethod
    def from_findings(cls, findings: list[Finding]) -> Verdict:
        level = max((f.level for f in findings), default=Level.PASS)
        return cls(level=level, findings=findings)

    def __str__(self) -> str:
        header = f"VERDICT: {self.level.name}"
        if not self.findings:
            return f"{header}\n  (no findings)"
        body = "\n".join(f.render() for f in self.findings)
        return f"{header}\n{body}"
