"""Spec Composer — the artifact-creation conductor.

One mechanism: `compose(request, pipeline)` (`engine.py`) drives a single
artifact through a declared create -> gate -> generate -> gate -> judge -> emit
lifecycle. The lifecycle itself is policy expressed as data — an ordered, typed
stage list in a pipeline contract (`contract.py`) that the sibling Linter
validates before the conductor runs it. Contract resolution, generation and
behavioral evaluation are injected structural seams (`protocol.py`), so the
engine holds no model vocabulary and spends no tokens.

`compose` and `judge_artifact` are exposed lazily: importing this package must
never pull in the OPTIONAL sibling `spec_judge`, so a judge-less pipeline,
`--check` and `--selfcheck` all work without it.
"""

from .contract import (
    JUDGE_TIERS,
    PRODUCING_KINDS,
    STAGE_KINDS,
    PipelineContract,
    PipelineDocument,
    PipelineSpec,
    Stage,
    bound_contract_name,
)
from .emit import EmitError, archive_spec, promote, resolve_archive_dir
from .generator import FakeGenerator, StagedArtifactGenerator
from .models import (
    ComposeRequest,
    ComposeResult,
    Disposition,
    GenerationOutcome,
    GenerationRequest,
    StageRecord,
    StageVerdict,
)
from .protocol import ContractResolver, Generator
from .resolver import DefaultResolver, UnresolvedContract
from .runstate import RunLog, digest, run_dir, run_root, workspace_root

__all__ = [
    "JUDGE_TIERS",
    "PRODUCING_KINDS",
    "STAGE_KINDS",
    "ComposeRequest",
    "ComposeResult",
    "ContractResolver",
    "DefaultResolver",
    "Disposition",
    "EmitError",
    "FakeGenerator",
    "GenerationOutcome",
    "GenerationRequest",
    "Generator",
    "PipelineContract",
    "PipelineDocument",
    "PipelineSpec",
    "RunLog",
    "Stage",
    "StageRecord",
    "StageVerdict",
    "StagedArtifactGenerator",
    "UnresolvedContract",
    "archive_spec",
    "bound_contract_name",
    "digest",
    "promote",
    "resolve_archive_dir",
    "run_dir",
    "run_root",
    "workspace_root",
]


def __getattr__(name: str) -> object:
    """`compose` and `judge_artifact` bind on first access, so `import
    spec_composer` never reaches the optional sibling Judger."""
    if name == "compose":
        from .engine import compose

        return compose
    if name == "judge_artifact":
        from .judging import judge_artifact

        return judge_artifact
    if name == "JudgeUnavailable":
        from .judging import JudgeUnavailable

        return JudgeUnavailable
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
