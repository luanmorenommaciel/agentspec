"""The pipeline contract — the Composer's own policy artifact.

`PipelineContract` implements the Linter's `Contract` protocol, so the
conductor's configuration is validated by the same engine it drives artifacts
through. `check` owns every rule id and its severity; `parse` stays permissive so
a defect is reported as a NAMED rule rather than collapsing into one opaque
`unparseable` finding. The ordering rules are SUBJECT-AWARE: each stage is
checked against the producing stage whose output it consumes, so a pipeline with
two generate/judge cycles is legal while every model-based stage still sits
behind a gate. `PipelineSpec` is the strict run-time view, built only from a
contract that did not FAIL.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError
from spec_linter import Finding, Level

JUDGE_TIERS = ("smoke", "standard", "high-assurance")
STAGE_KINDS = ("create", "lint", "generate", "judge", "emit")
PRODUCING_KINDS = ("create", "generate")

_DEFAULT_KNOWN = frozenset({"creation-spec", "agent-spec"})


class StageDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    id: str | None = None
    kind: str | None = None
    input_contract: str | None = None
    output_contract: str | None = None
    judge_tier: str | None = None
    require_approval_for: tuple[str, ...] = ()


class PipelineDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    pipeline: str | None = None
    version: int | None = None
    max_attempts: Any = None
    archive: str | None = None
    stages: tuple[StageDocument, ...] = ()


def _fail(rule: str, field: str, message: str, expected: str, found: str) -> Finding:
    return Finding(
        level=Level.FAIL, rule=rule, field=field, message=message, expected=expected, found=found
    )


def _warn(rule: str, field: str, message: str) -> Finding:
    return Finding(level=Level.WARN, rule=rule, field=field, message=message)


def _schema_message(error: ValidationError) -> str:
    parts = []
    for err in error.errors():
        field = ".".join(str(part) for part in err["loc"]) or "<root>"
        parts.append(f"{field}: {err['msg']} [{err['type']}]")
    return "pipeline contract is not well-formed — " + "; ".join(parts)


def _label(stage: StageDocument, index: int) -> str:
    return stage.id or stage.kind or f"stages[{index}]"


def _preceding_producer(stages: tuple[StageDocument, ...], index: int) -> int:
    """Index of the closest producing stage before `index`, or -1."""
    for position in range(index - 1, -1, -1):
        if stages[position].kind in PRODUCING_KINDS:
            return position
    return -1


def _has_gate_between(stages: tuple[StageDocument, ...], start: int, end: int) -> bool:
    return any(stage.kind == "lint" for stage in stages[start + 1 : end])


def shape_findings(doc: PipelineDocument) -> list[Finding]:
    findings: list[Finding] = []
    for field in ("pipeline", "version", "stages"):
        if getattr(doc, field) in (None, (), ""):
            findings.append(
                _fail(
                    "P1.missing_field",
                    field,
                    f"required field '{field}' is missing or empty",
                    "present",
                    "absent",
                )
            )
    budget = doc.max_attempts
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
        findings.append(
            _fail(
                "P1.max_attempts",
                "max_attempts",
                "max_attempts is the TOTAL number of generation attempts per artifact "
                "(one initial attempt plus repairs) and must be an integer of at least 1",
                ">= 1",
                repr(budget),
            )
        )
    template = doc.archive
    if template is not None and (Path(template).is_absolute() or ".." in Path(template).parts):
        findings.append(
            _fail(
                "P1.archive_template",
                "archive",
                "the archive template must be relative and must not escape the workspace root; "
                "an invalid template ends the run in error before any stage can run",
                "a relative path with no '..' segment",
                repr(template),
            )
        )
    seen: set[str] = set()
    for index, stage in enumerate(doc.stages):
        label = _label(stage, index)
        if stage.kind not in STAGE_KINDS:
            findings.append(
                _fail(
                    "P1.unknown_kind",
                    label,
                    f"stage kind {stage.kind!r} is not a pipeline stage kind",
                    " | ".join(STAGE_KINDS),
                    repr(stage.kind),
                )
            )
        if stage.id is None:
            findings.append(
                _fail("P1.missing_field", label, "a stage must declare an id", "present", "absent")
            )
        elif stage.id in seen:
            findings.append(
                _fail(
                    "P1.duplicate_stage_id",
                    stage.id,
                    f"stage id {stage.id!r} is declared more than once",
                    "unique",
                    "duplicate",
                )
            )
        else:
            seen.add(stage.id)
        findings += [
            _warn(
                "P1.unknown_field",
                f"{label}.{key}",
                f"unknown stage key {key!r} is ignored by the conductor",
            )
            for key in sorted(stage.model_extra or {})
        ]
    findings += [
        _warn("P1.unknown_field", key, f"unknown top-level key {key!r} is ignored by the conductor")
        for key in sorted(doc.model_extra or {})
    ]
    return findings


def ordering_findings(doc: PipelineDocument) -> list[Finding]:
    """The ADR ordering invariant as CHECKED, subject-aware rules: a contract
    that violates it is expressible, and must FAIL."""
    findings: list[Finding] = []
    stages = doc.stages
    for index, stage in enumerate(stages):
        label = _label(stage, index)
        if stage.kind == "judge":
            producer = _preceding_producer(stages, index)
            if producer < 0:
                findings.append(
                    _fail(
                        "P2.judge_without_subject",
                        label,
                        "a judge stage has no upstream stage that produces an artifact",
                        "a create or generate stage upstream",
                        "none",
                    )
                )
            elif not _has_gate_between(stages, producer, index):
                findings.append(
                    _fail(
                        "P2.judge_after_gates",
                        label,
                        "a model-based stage would run before the deterministic gate on its "
                        "own subject; the cheap gate must clear first",
                        "a lint stage between the producing stage and the judge",
                        "no lint stage between "
                        f"{_label(stages[producer], producer)!r} and this one",
                    )
                )
        elif stage.kind == "generate":
            origin = -1
            for position in range(index - 1, -1, -1):
                if stages[position].kind == "create":
                    origin = position
                    break
            if not _has_gate_between(stages, origin, index):
                findings.append(
                    _fail(
                        "P2.generate_gated",
                        label,
                        "generation would run on a spec that was never gated",
                        "a lint stage before the generate stage",
                        "none",
                    )
                )
        elif stage.kind == "emit":
            producer = _preceding_producer(stages, index)
            if producer < 0 or not _has_gate_between(stages, producer, index):
                findings.append(
                    _fail(
                        "P2.emit_gated",
                        label,
                        "an artifact would be promoted ungated; anything a model produced "
                        "must clear a gate before emission",
                        "a producing stage and then a lint stage before the emit",
                        "none" if producer < 0 else "no lint stage after the producing stage",
                    )
                )
            if index != len(stages) - 1:
                findings.append(
                    _fail(
                        "P2.emit_last",
                        label,
                        "an emit stage must be the final stage",
                        f"position {len(stages) - 1}",
                        f"position {index}",
                    )
                )
    return findings


def binding_findings(doc: PipelineDocument, known: frozenset[str]) -> list[Finding]:
    """Contract-reference rules. A `create` stage's `input_contract` is exempt from
    the chain rule: what a create stage consumes is the REQUEST, which no upstream
    stage produces, so naming one describes an origin rather than an unbound
    reference."""
    findings: list[Finding] = []
    produced: set[str] = set()
    for index, stage in enumerate(doc.stages):
        label = _label(stage, index)
        if stage.kind != "create" and stage.input_contract and stage.input_contract not in produced:
            findings.append(
                _fail(
                    "P3.stage_io_chain",
                    label,
                    f"input_contract {stage.input_contract!r} is not produced by "
                    "any upstream stage",
                    "produced upstream",
                    "unbound",
                )
            )
        if stage.kind == "judge" and stage.judge_tier not in JUDGE_TIERS:
            findings.append(
                _fail(
                    "P3.judge_tier",
                    label,
                    "a judge stage must declare a known independence tier",
                    " | ".join(JUDGE_TIERS),
                    repr(stage.judge_tier),
                )
            )
        for name in (stage.input_contract, stage.output_contract):
            if name and name not in known:
                findings.append(
                    _warn(
                        "P3.dangling_reference",
                        label,
                        f"contract {name!r} has no default binding; the run reports "
                        "an error unless a resolver supplies it",
                    )
                )
        if stage.kind in PRODUCING_KINDS and stage.output_contract:
            produced.add(stage.output_contract)
    return findings


class PipelineContract:
    def __init__(self, known_contracts: frozenset[str] | None = None) -> None:
        self.name = "pipeline-contract"
        self._known = _DEFAULT_KNOWN if known_contracts is None else known_contracts

    def parse(self, artifact: Any) -> PipelineDocument:
        if not isinstance(artifact, dict):
            raise TypeError("a pipeline contract must be a YAML mapping at the top level")
        try:
            return PipelineDocument.model_validate(artifact)
        except ValidationError as exc:
            raise ValueError(_schema_message(exc)) from exc

    def check(self, parsed: PipelineDocument) -> list[Finding]:
        findings = shape_findings(parsed)
        findings += ordering_findings(parsed)
        findings += binding_findings(parsed, self._known)
        return findings


class Stage(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: Literal["create", "lint", "generate", "judge", "emit"]
    input_contract: str | None = None
    output_contract: str | None = None
    judge_tier: str | None = None
    require_approval_for: tuple[str, ...] = ()


class PipelineSpec(BaseModel):
    """The strict run-time view. Build it only after `lint(data, PipelineContract())`
    returned a non-FAIL verdict: a FAIL is an operational error, not a run."""

    model_config = ConfigDict(frozen=True)

    pipeline: str
    version: int
    max_attempts: int
    archive: str | None = None
    stages: tuple[Stage, ...]

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> PipelineSpec:
        return cls.model_validate(data)


def bound_contract_name(stage: Stage) -> str:
    """The name folded into a stamp's digests — KIND-AWARE, because `generate`
    declares both an input and an output contract and must bind to the one it
    produces, or its digests would collide with the preceding gate's."""
    if stage.kind in PRODUCING_KINDS:
        return stage.output_contract or stage.kind
    if stage.kind == "lint":
        return stage.input_contract or stage.kind
    if stage.kind == "judge":
        return "spec-conformance"
    return "emit"
