"""Contract protocol — the interface the engine validates against.

A Contract is pure policy: it declares WHAT is checked and assigns severity to
its own rules. The engine (engine.py) is pure mechanism: it runs a contract
against an artifact and assembles the Verdict. Neither knows any usage context.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .verdict import Finding


@runtime_checkable
class Contract(Protocol):
    name: str

    def parse(self, artifact: Any) -> Any:
        """Turn a raw artifact (mapping, text, path-loaded data) into a
        checkable object, or raise to signal an unparseable artifact."""
        ...

    def check(self, parsed: Any) -> list[Finding]:
        """Return findings for a successfully parsed artifact. Each finding
        carries this contract's chosen severity (Level)."""
        ...
