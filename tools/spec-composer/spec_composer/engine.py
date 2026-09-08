"""The conductor — deterministic and token-free.

`compose` folds the on-disk evidence, sequences the pipeline's stages, stamps
every verdict it obtains, routes a gate FAIL back to the nearest preceding
producing stage, accounts the shared generation budget, and escalates when it
runs out. No model is invoked here: every model call happens inside an injected
seam.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import ValidationError
from spec_linter import Finding, Level, Verdict, lint
from spec_linter.frontmatter import FrontmatterError, split_frontmatter

from .contract import PRODUCING_KINDS, PipelineSpec, Stage, bound_contract_name
from .emit import EmitError, archive_spec, promote, resolve_archive_dir
from .generator import StagedArtifactGenerator
from .judging import JudgeUnavailableError, judge_artifact
from .models import (
    ComposeRequest,
    ComposeResult,
    Disposition,
    GenerationRequest,
    StageRecord,
    StageVerdict,
)
from .protocol import ContractResolver, Generator
from .resolver import DefaultResolver
from .runstate import RunLog, digest, now, run_dir, slug

if TYPE_CHECKING:
    from spec_judge import Evaluator

_PASS = Verdict.from_findings([])
_SETTLED = (Level.PASS.name, Level.WARN.name)

# A producing stage whose expected output is byte-identical to content a gate
# already rejected is not making progress. The first such wait is left
# uncapped: per USAGE.md's host-loop guidance, a host may legitimately re-run
# the identical command without having regenerated anything yet (a slow host,
# a re-run out of habit), and that costs nothing. A second occurrence at the
# same stage means it was presented the same already-stamped bytes again, with
# nothing new in between — that carries no new information, so this one blocks
# instead of waiting. Two, not more.
STALE_WAIT_CEILING = 2


@dataclass(frozen=True, slots=True)
class Step:
    """What one stage dispatch reports back to the loop.

    `stamped` marks a step that already wrote its own stamp. The emit stage does,
    because it can only hash what it promoted after the promotion succeeded.
    """

    verdict: Verdict | None = None
    disposition: Disposition | None = None
    reason: str | None = None
    path: Path | None = None
    stamped: bool = False


def nearest_producer(pipeline: PipelineSpec, index: int) -> tuple[int, Stage | None]:
    """The feedback target and the artifact source, derived from position: the
    closest `create` or `generate` stage before `index`. Returns the INDEX with
    the stage — never a value lookup, so two structurally identical stages
    cannot mis-resolve to each other."""
    for position in range(index - 1, -1, -1):
        if pipeline.stages[position].kind in PRODUCING_KINDS:
            return position, pipeline.stages[position]
    return -1, None


def _finding_rows(findings: Iterable[Finding]) -> tuple[dict[str, Any], ...]:
    return tuple({**item.model_dump(mode="json"), "level": item.level.name} for item in findings)


def _findings_from_rows(rows: Iterable[dict[str, Any]]) -> tuple[Finding, ...]:
    restored: list[Finding] = []
    for row in rows:
        data = dict(row)
        level = data.get("level")
        if isinstance(level, str):
            data["level"] = Level[level]
        try:
            restored.append(Finding.model_validate(data))
        except ValidationError:
            continue
    return tuple(restored)


def _load_mapping(path: Path) -> Any:
    """The subject of a gate, as the contract expects to receive it: a mapping
    from a Markdown artifact's frontmatter, or from a YAML document. Anything
    else is returned untouched so the contract — not this loader — decides that
    the artifact is unparseable."""
    text = path.read_text(encoding="utf-8")
    try:
        data, _ = split_frontmatter(text)
    except FrontmatterError:
        return text
    if data is not None:
        return data
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return text


class RunContext:
    """Everything one run needs: the folded state, the two digests, the three
    resume rules, and the append-only writes."""

    def __init__(
        self,
        request: ComposeRequest,
        pipeline_contract: PipelineSpec,
        directory: Path,
        log: RunLog,
        archive_dir: Path,
    ) -> None:
        self.request = request
        self.pipeline = pipeline_contract
        self.run_dir = directory
        self.log = log
        self.archive_dir = archive_dir
        folded = log.fold()
        self.epoch = folded.epoch
        self.attempts_spent = folded.attempts_spent
        self.attempt = folded.attempt
        self.approvals: set[str] = set(folded.approvals)
        self.trail: list[StageVerdict] = []
        self.published: dict[str, Path] = {}
        self.last_reason: str | None = None
        self._payloads: dict[str, Path] = {}
        self._stamps: list[StageRecord] = list(folded.stamps)
        self._epoch_stamps: list[StageRecord] = list(folded.epoch_stamps)
        self._last_spend: StageRecord | None = folded.last_spend
        self._stale_waits: dict[str, int] = dict(folded.stale_waits)
        self._artifact: Path | None = None

    @classmethod
    def open(cls, request: ComposeRequest, pipeline_contract: PipelineSpec) -> RunContext:
        """Resolve the run directory from the target, validate the archive
        template (relative, inside the workspace) BEFORE any stage runs, fold the
        log, and record any approvals this invocation granted."""
        directory = run_dir(pipeline_contract.pipeline, request.target)
        archive_dir = resolve_archive_dir(request.name, pipeline_contract.archive)
        context = cls(
            request, pipeline_contract, directory, RunLog(directory / "run.jsonl"), archive_dir
        )
        context._grant(request.approvals)
        return context

    @property
    def spec_path(self) -> Path:
        """`request.spec_path`, or `<run>/spec/{name}.spec.md` when the operator
        supplied none. Never attempt-scoped."""
        if self.request.spec_path is not None:
            return self.request.spec_path
        return self.run_dir / "spec" / f"{slug(self.request.name)}.spec.md"

    @property
    def artifact(self) -> Path | None:
        if self._artifact is not None:
            return self._artifact
        target = self.request.target
        return target if target.is_file() else None

    def output_path(self, stage: Stage) -> Path:
        """Where this stage writes when it actually runs: `create` -> the fixed
        spec path; `generate` -> the attempt-scoped AND stage-scoped
        `<run>/staging/attempt-{n}/{stage}/{basename}`, so two producing stages in
        one pipeline can never overwrite each other's output."""
        if stage.kind == "create":
            return self.spec_path
        return (
            self.run_dir
            / "staging"
            / f"attempt-{self.attempt}"
            / slug(stage.id)
            / self.request.target.name
        )

    def payload_path(self, stage: Stage) -> Path:
        """Where this stage's output actually lives right now: the path recorded
        on the stamp it was resolved from when the stage skipped, and the path it
        wrote to otherwise."""
        return self._payloads.get(stage.id) or self.output_path(stage)

    def input_path(self, stage: Stage) -> Path | None:
        if stage.kind == "create":
            return None
        if stage.input_contract:
            published = self.published.get(stage.input_contract)
            if published is not None:
                return published
        return self.spec_path if stage.kind == "generate" else None

    def subject_path(self, stage: Stage, index: int) -> Path:
        """What this stage reads: the path PUBLISHED for the contract it consumes,
        falling back to the producing stage's current output path only when nothing
        was published. Resolving through the published path is what lets a skipped
        producer hand a downstream stage the artifact its own stamp certified,
        rather than an attempt-scoped path that may not exist this run."""
        if stage.kind == "lint":
            path = self.input_path(stage)
            if path is None:
                raise ValueError(
                    f"stage {stage.id!r} consumes {stage.input_contract!r}, "
                    "which no upstream stage published"
                )
            return path
        _, producer = nearest_producer(self.pipeline, index)
        if producer is None:
            raise ValueError(f"stage {stage.id!r} has no upstream stage that produces an artifact")
        if producer.output_contract:
            published = self.published.get(producer.output_contract)
            if published is not None:
                return published
        return self.payload_path(producer)

    def _subject_bytes(self, stage: Stage, index: int) -> bytes | None:
        if stage.kind == "create":
            return b""
        try:
            path = (
                self.input_path(stage)
                if stage.kind == "generate"
                else self.subject_path(stage, index)
            )
        except ValueError:
            return None
        if path is None or not path.is_file():
            return None
        return path.read_bytes()

    def input_digest(self, stage: Stage, index: int) -> str | None:
        content = self._subject_bytes(stage, index)
        if content is None:
            return None
        return digest(
            content,
            contract_version=self.pipeline.version,
            contract_name=bound_contract_name(stage),
        )

    def output_digest(self, stage: Stage, content: bytes) -> str:
        return digest(
            content,
            contract_version=self.pipeline.version,
            contract_name=bound_contract_name(stage),
        )

    def is_pending(self, stage: Stage) -> bool:
        """The last `spend` row of this epoch routed here AND no stamp exists for
        this stage at the current attempt."""
        if self._last_spend is None or self._last_spend.route_to != stage.id:
            return False
        return not any(
            row.stage == stage.id and row.attempt == self.attempt for row in self._epoch_stamps
        )

    def settled_stamps(self, stage: Stage) -> list[StageRecord]:
        """This stage's stamps that certify something: PASS or WARN only. A FAIL
        never certifies, and neither does a row whose verdict is absent or foreign
        — a torn or hand-edited log must not be able to grant a skip."""
        return [row for row in self._stamps if row.stage == stage.id and row.verdict in _SETTLED]

    def stamped_payload(self, stage: Stage, expected_input: str) -> Path | None:
        """The payload a producing stage's own evidence still vouches for: the most
        recent settled stamp made from THIS input whose recorded path still holds
        the bytes that stamp certified. Resolving the payload from the stamp — not
        from the current attempt number — is what lets a finished stage stay
        finished across epochs."""
        for row in reversed(self.settled_stamps(stage)):
            if row.input_hash != expected_input or row.path is None or row.output_hash is None:
                continue
            payload = Path(row.path)
            if not payload.is_file():
                continue
            if self.output_digest(stage, payload.read_bytes()) == row.output_hash:
                return payload
        return None

    def target_is_stamped(self, stage: Stage) -> bool:
        """The emit target holds bytes some emit stamp already certified."""
        target = self.request.target
        if not target.is_file():
            return False
        promoted = self.output_digest(stage, target.read_bytes())
        return any(row.output_hash == promoted for row in self.settled_stamps(stage))

    def target_holds_the_subject(self, stage: Stage, index: int) -> bool:
        """The emit target already holds exactly the bytes this run would promote.
        A stamp alone cannot answer that: it says the target was promoted at some
        point, not that it matches the artifact standing behind THIS run — so a
        regenerated artifact that cleared every gate would otherwise be stamped,
        reported `emitted`, and never actually written."""
        target = self.request.target
        if not target.is_file():
            return False
        try:
            subject = self.subject_path(stage, index)
        except ValueError:
            return False
        return subject.is_file() and target.read_bytes() == subject.read_bytes()

    def target_was_modified(self, stage: Stage, staged: Path) -> bool:
        """The emit target holds bytes no emit stamp certifies, and they are not the
        staged bytes either: the canonical artifact was edited in place after this
        pipeline last promoted it, or it belongs to something else entirely.
        Promoting over it would destroy work no evidence accounts for."""
        if not self.request.target.is_file() or self.target_is_stamped(stage):
            return False
        target_bytes = self.request.target.read_bytes()
        return not staged.is_file() or staged.read_bytes() != target_bytes

    def skips(self, stage: Stage, index: int) -> bool:
        """False for a pending stage. Otherwise: a settled stamp exists whose
        digests match what is on disk now. A skipped producing stage also records
        the payload its stamp resolved to, so `register` publishes that file rather
        than a path this run never wrote."""
        if self.is_pending(stage):
            return False
        if not self.settled_stamps(stage):
            return False
        if stage.kind == "emit":
            return self.target_holds_the_subject(stage, index) and self.target_is_stamped(stage)
        expected_input = self.input_digest(stage, index)
        if expected_input is None:
            return False
        if stage.kind in PRODUCING_KINDS:
            payload = self.stamped_payload(stage, expected_input)
            if payload is None:
                return False
            self._payloads[stage.id] = payload
            return True
        return any(row.input_hash == expected_input for row in self.settled_stamps(stage))

    def is_fresh(self, stage: Stage, output_hash: str) -> bool:
        """This stage has never stamped that `output_hash` — in ANY epoch. A new
        epoch resets the budget, never the evidence: re-presenting content a gate
        already judged would replay a whole spent budget over artifacts that were
        already rejected."""
        return not any(
            row.stage == stage.id and row.output_hash == output_hash for row in self._stamps
        )

    def stale_waits(self, stage: Stage) -> int:
        """`stale-artifact` waits this stage has accumulated since its last
        stamp in the current epoch, folded from the log — 0 until the first
        one. Not truly "consecutive": an intervening `awaiting-artifact` event
        at this stage neither resets nor increments the count — only a stamp
        resets it (see `RunLog.fold`, and the reset kept in step with it inside
        `stamp`). `_produce` compares this count against `STALE_WAIT_CEILING` to
        decide whether one more wait is still warranted or the run must stop
        instead."""
        return self._stale_waits.get(stage.id, 0)

    def feedback_for(self, stage: Stage) -> tuple[Finding, ...]:
        if self._last_spend is None or self._last_spend.route_to != stage.id:
            return ()
        return _findings_from_rows(self._last_spend.findings)

    def spec_mapping(self) -> dict[str, Any]:
        path = self.spec_path
        if not path.is_file():
            return {}
        loaded = _load_mapping(path)
        return loaded if isinstance(loaded, dict) else {}

    def register(self, stage: Stage, _index: int) -> None:
        """Publish the file a producing stage's output CONTRACT now refers to —
        the path its stamp resolved to when it skipped, the path it wrote to when
        it ran — so every downstream `input_contract` reference reads the artifact
        that was actually certified."""
        if stage.kind in PRODUCING_KINDS and stage.output_contract:
            self.published[stage.output_contract] = self.payload_path(stage)

    def stamp(
        self, stage: Stage, index: int, verdict: Verdict, output_hash: str | None = None
    ) -> None:
        """Append a `stamp` row, extend the in-memory trail, and reset this
        stage's stale-wait count to 0 — the same reset `RunLog.fold` applies to
        a `stamp` row (see there). `_stale_waits` is a snapshot taken once, at
        `RunContext.__init__`; without this, a stamp appended later in the SAME
        process (a repair loop that cycles back in-process, e.g. after a Gate A
        FAIL routes to `create`) would leave that snapshot stale, so a later
        call to `stale_waits` in this process would read a count the log no
        longer supports. Keeping `_stale_waits` current here, the way `_stamps`
        and `_last_spend` already are below, is what keeps this method's
        contract true: the count `stale_waits` returns must always equal what
        folding the log fresh would give at that instant, in-process or not."""
        resolved = output_hash
        payload: Path | None = None
        if stage.kind in PRODUCING_KINDS:
            payload = self.output_path(stage)
            self._payloads[stage.id] = payload
            if resolved is None and payload.is_file():
                resolved = self.output_digest(stage, payload.read_bytes())
        record = StageRecord(
            ts=now(),
            kind="stamp",
            stage=stage.id,
            stage_kind=stage.kind,
            attempt=self.attempt,
            attempts_spent=self.attempts_spent,
            verdict=verdict.level.name,
            input_hash=self.input_digest(stage, index),
            output_hash=resolved,
            contract_id=f"{bound_contract_name(stage)}@{self.pipeline.version}",
            path=str(payload) if payload is not None else None,
            findings=_finding_rows(verdict.findings),
        )
        self.log.append(record)
        self._stamps.append(record)
        self._epoch_stamps.append(record)
        self._stale_waits[stage.id] = 0
        self.trail.append(
            StageVerdict(
                stage=stage.id,
                stage_kind=stage.kind,
                contract=bound_contract_name(stage),
                attempt=self.attempt,
                verdict=verdict,
            )
        )

    def route(self, stage: Stage, index: int, verdict: Verdict) -> int:
        """Charge the shared budget, then record the route — in that order, so the
        evidence never claims a route that was not taken."""
        target_index, target = nearest_producer(self.pipeline, index)
        if target is None:
            self.spend(stage, route_to=None, reason="no-feedback-target", verdict=verdict)
            return -1
        if self.attempts_spent + 1 >= self.pipeline.max_attempts:
            self.spend(stage, route_to=None, reason="budget-exhausted", verdict=verdict)
            return -1
        self.spend(stage, route_to=target.id, reason=None, verdict=verdict)
        return target_index

    def spend(
        self, stage: Stage, *, route_to: str | None, reason: str | None, verdict: Verdict
    ) -> None:
        """Append a `spend` row carrying the derived target and the findings."""
        self.attempts_spent += 1
        self.attempt = self.attempts_spent + 1
        record = StageRecord(
            ts=now(),
            kind="spend",
            stage=stage.id,
            stage_kind=stage.kind,
            attempt=self.attempt,
            attempts_spent=self.attempts_spent,
            verdict=verdict.level.name,
            reason=reason,
            route_to=route_to,
            findings=_finding_rows(verdict.findings),
        )
        self.log.append(record)
        self._last_spend = record
        self.last_reason = reason

    def event(
        self,
        reason: str | None,
        stage: Stage | None,
        *,
        disposition: str | None = None,
        path: Path | None = None,
        detail: str | None = None,
    ) -> None:
        self.log.append(
            StageRecord(
                ts=now(),
                kind="event",
                stage=stage.id if stage is not None else "",
                stage_kind=stage.kind if stage is not None else "",
                attempt=self.attempt,
                attempts_spent=self.attempts_spent,
                disposition=disposition,
                reason=reason,
                path=str(path) if path is not None else None,
                detail=detail,
            )
        )

    def archive(self) -> Path:
        return archive_spec(
            self.archive_dir,
            self.spec_path,
            {
                "pipeline": self.pipeline.pipeline,
                "version": self.pipeline.version,
                "epoch": self.epoch,
                "attempts_spent": self.attempts_spent,
                "target": str(self.request.target.expanduser().resolve()),
                "stamps": [
                    {
                        "stage": row.stage,
                        "kind": row.stage_kind,
                        "attempt": row.attempt,
                        "verdict": row.verdict,
                        "contract_id": row.contract_id,
                        "input_hash": row.input_hash,
                        "output_hash": row.output_hash,
                    }
                    for row in self._epoch_stamps
                ],
            },
        )

    def mark_emitted(self) -> None:
        self._artifact = self.request.target

    def finish(
        self,
        disposition: Disposition,
        stage: Stage | None,
        reason: str | None,
        path: Path | None,
        verdict: Verdict | None,
    ) -> ComposeResult:
        """Append the terminal `event`; append `run-closed` for `emitted` and
        `blocked` only, so a `waiting` or `paused` re-run continues the same epoch
        with the same budget."""
        if (
            verdict is not None
            and stage is not None
            and (not self.trail or self.trail[-1].verdict != verdict)
        ):
            self.trail.append(
                StageVerdict(
                    stage=stage.id,
                    stage_kind=stage.kind,
                    contract=bound_contract_name(stage),
                    attempt=self.attempt,
                    verdict=verdict,
                )
            )
        self.event(reason, stage, disposition=disposition.value, path=path)
        if disposition in (Disposition.EMITTED, Disposition.BLOCKED):
            self.log.append(
                StageRecord(
                    ts=now(),
                    kind="run-closed",
                    stage=stage.id if stage is not None else "",
                    stage_kind=stage.kind if stage is not None else "",
                    attempt=self.attempt,
                    attempts_spent=self.attempts_spent,
                    disposition=disposition.value,
                    reason=reason,
                )
            )
        emitted = disposition is Disposition.EMITTED
        return ComposeResult(
            disposition=disposition,
            stage=stage.id if stage is not None else None,
            epoch=self.epoch,
            attempt=self.attempt,
            attempts_spent=self.attempts_spent,
            trail=tuple(self.trail),
            run_dir=self.run_dir,
            artifact=self.artifact if emitted else None,
            expected_path=None if emitted else path,
            reason=reason,
        )

    def _grant(self, classes: frozenset[str]) -> None:
        if not classes:
            return
        self.approvals |= set(classes)
        self.log.append(
            StageRecord(
                ts=now(),
                kind="approval",
                stage="",
                stage_kind="",
                attempt=self.attempt,
                attempts_spent=self.attempts_spent,
                approvals=tuple(sorted(classes)),
            )
        )


def _produce(stage: Stage, _index: int, run: RunContext, generator: Generator) -> Step:
    output_path = run.output_path(stage)
    input_path = run.input_path(stage)
    input_text = ""
    if input_path is not None and input_path.is_file():
        input_text = input_path.read_text(encoding="utf-8")
    outcome = generator.generate(
        GenerationRequest(
            stage=stage.id,
            kind=stage.kind,
            output_contract=stage.output_contract,
            output_path=output_path,
            attempt=run.attempt,
            input_path=input_path,
            input_text=input_text,
            feedback=run.feedback_for(stage),
        )
    )
    if not outcome.produced or not outcome.path.is_file():
        return Step(disposition=Disposition.WAITING, reason="awaiting-artifact", path=output_path)
    produced = run.output_digest(stage, outcome.path.read_bytes())
    if not run.is_fresh(stage, produced):
        if run.stale_waits(stage) + 1 >= STALE_WAIT_CEILING:
            # Unlike every other WAITING/BLOCKED disposition, there is nothing
            # for the operator to write here — the stage is stopping BECAUSE
            # the expected path already holds content, not because it is
            # missing one. No `path`, so the CLI never prints "expected at:".
            return Step(disposition=Disposition.BLOCKED, reason="no-progress", path=None)
        return Step(disposition=Disposition.WAITING, reason="stale-artifact", path=output_path)
    return Step(verdict=_PASS)


def _gate(stage: Stage, index: int, run: RunContext, resolver: ContractResolver) -> Step:
    contract = resolver.resolve(stage.input_contract or stage.kind)
    subject = run.subject_path(stage, index)
    if not subject.is_file():
        return Step(disposition=Disposition.WAITING, reason="awaiting-artifact", path=subject)
    return Step(verdict=lint(_load_mapping(subject), contract))


def _judge(stage: Stage, index: int, run: RunContext, evaluator: Evaluator | None) -> Step:
    subject = run.subject_path(stage, index)
    if not subject.is_file():
        return Step(disposition=Disposition.WAITING, reason="awaiting-artifact", path=subject)
    mapping = run.spec_mapping()
    source_spec = {**mapping, "id": mapping.get("id") or run.request.name}
    try:
        verdict = judge_artifact(
            subject.read_text(encoding="utf-8"),
            source_spec,
            tier=stage.judge_tier or "standard",
            evaluator=evaluator,
        )
    except JudgeUnavailableError:
        return Step(disposition=Disposition.PAUSED, reason="judge-unavailable")
    if verdict.level is Level.FAIL:
        if any(finding.rule.endswith(".unparseable") for finding in verdict.findings):
            return Step(verdict=verdict, disposition=Disposition.ERROR, reason="judge-unparseable")
        if stage.judge_tier == "high-assurance":
            return Step(
                verdict=verdict, disposition=Disposition.BLOCKED, reason="high-assurance-judge-fail"
            )
        return Step(verdict=verdict, disposition=Disposition.ERROR, reason="judge-unparseable")
    return Step(verdict=verdict)


def _emit(stage: Stage, index: int, run: RunContext) -> Step:
    outstanding = [name for name in stage.require_approval_for if name not in run.approvals]
    if outstanding:
        return Step(disposition=Disposition.PAUSED, reason=f"approval-outstanding:{outstanding[0]}")
    staged = run.subject_path(stage, index)
    if run.target_was_modified(stage, staged):
        return Step(disposition=Disposition.PAUSED, reason="target-modified")
    try:
        promote(staged, run.request.target)
    except EmitError as exc:
        run.event("promotion-failed", stage, detail=str(exc))
        return Step(disposition=Disposition.ERROR, reason="promotion-failed")
    run.stamp(
        stage, index, _PASS, output_hash=run.output_digest(stage, run.request.target.read_bytes())
    )
    run.mark_emitted()
    try:
        run.archive()
    except (OSError, ValueError) as exc:
        run.event("archive-failed", stage, detail=str(exc))
    return Step(verdict=_PASS, stamped=True)


def dispatch(
    stage: Stage,
    index: int,
    run: RunContext,
    resolver: ContractResolver,
    generator: Generator,
    evaluator: Evaluator | None,
) -> Step:
    if stage.kind in PRODUCING_KINDS:
        return _produce(stage, index, run, generator)
    if stage.kind == "lint":
        return _gate(stage, index, run, resolver)
    if stage.kind == "judge":
        return _judge(stage, index, run, evaluator)
    return _emit(stage, index, run)


def compose(
    request: ComposeRequest,
    pipeline_contract: PipelineSpec,
    *,
    resolver: ContractResolver | None = None,
    generator: Generator | None = None,
    evaluator: Evaluator | None = None,
) -> ComposeResult:
    resolver = resolver or DefaultResolver()
    generator = generator or StagedArtifactGenerator()
    run = RunContext.open(request, pipeline_contract)

    index = 0
    while index < len(pipeline_contract.stages):
        stage = pipeline_contract.stages[index]

        if run.skips(stage, index):
            run.register(stage, index)
            index += 1
            continue

        step = dispatch(stage, index, run, resolver, generator, evaluator)

        if step.verdict is not None and not step.stamped:
            run.stamp(stage, index, step.verdict)

        if step.disposition is not None:
            return run.finish(step.disposition, stage, step.reason, step.path, step.verdict)

        if step.verdict is not None and step.verdict.level is Level.FAIL:
            index = run.route(stage, index, step.verdict)
            if index < 0:
                return run.finish(Disposition.BLOCKED, stage, run.last_reason, None, step.verdict)
            continue

        run.register(stage, index)
        index += 1

    last = pipeline_contract.stages[-1] if pipeline_contract.stages else None
    return run.finish(Disposition.EMITTED, last, None, run.artifact, None)
