"""Spec Linter — contract-validation engine (Gate A prototype for AgentSpec).

One mechanism: `lint(artifact, contract) -> Verdict` (`engine.py`). Contracts
are policy (`protocol.py` + `contracts/`); `Verdict` / `Finding` / `Level` are
the structured result. `AgentSpec` is the Pydantic model behind the agent-spec
reference contract and its JSON Schema.
"""

from .contracts.agent_spec import AgentSpecContract, emit_json_schema
from .contracts.instance import InstanceContract
from .contracts.sdd_phase import SddPhaseContract
from .engine import lint
from .models import AgentSpec
from .protocol import Contract
from .verdict import Finding, Level, Verdict

__all__ = [
    "AgentSpec",
    "AgentSpecContract",
    "Contract",
    "Finding",
    "InstanceContract",
    "Level",
    "SddPhaseContract",
    "Verdict",
    "emit_json_schema",
    "lint",
]
