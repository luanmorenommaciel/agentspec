# Spec Composer — Usage

The **Composer** is a deterministic, token-free conductor for artifact creation: it drives one artifact through a lifecycle declared as data — a pipeline contract — and never calls a model itself. This document is **normative** about what the engine does and what its dispositions and exit codes mean, and **suggestive** about how you might use it. The usage choice belongs to the consumer.

## 1. What it is (BINDING)

One entry point:

```python
# compose(request, pipeline_contract, *, resolver=None, generator=None, evaluator=None) -> ComposeResult
from spec_composer import compose
from spec_composer.contract import PipelineSpec
```

`compose` folds the on-disk evidence for this (pipeline, target) pair, walks the pipeline's declared stages in order, dispatches each by its `kind` (`create | lint | generate | judge | emit`), stamps whatever verdict it obtains, and either advances, routes a failure back to the nearest stage that can produce a fix, or stops and returns a `ComposeResult` carrying a `Disposition` (§3). Every non-deterministic concern — resolving a contract name, producing a `create`/`generate` stage's output, evaluating an artifact behaviorally — is an injected seam (§4); the conductor itself holds no model vocabulary and spends no tokens.

`spec_composer` reuses the sibling `spec-linter`'s `Verdict` / `Finding` / `Level` — imported, never re-declared — so a `lint` stage's outcome is exactly what `spec-linter` itself would report for the same artifact and contract. The sibling `spec-judge` is optional and imported lazily: `import spec_composer` never touches it, and `compose` / `judge_artifact` bind to it only on first access, so a judge-less pipeline, `--check`, and `--selfcheck` all work with `spec-judge` absent from the installation.

An exception escaping `compose()` (`UnresolvedContractError`, `EmitError`, a `ValueError` from a malformed contract, or any unexpected error) is different from a `Disposition`, which is an outcome the run reached and appended to its own evidence log (§6). The CLI maps both onto the same five-code exit surface, but only a `Disposition` closes a run: an escaping exception leaves no terminal record for this invocation, and a re-run resumes from whatever the log already holds.

## 2. The pipeline contract (BINDING shape, the lifecycle is policy)

The lifecycle a run drives is never hardcoded — it is declared as data, in a pipeline contract: a YAML mapping read by `spec-compose` and validated before a single stage runs.

```yaml
pipeline: <id>                 # string identity; also the first path segment of the run directory
version: <int>                 # the rule version in force — folded into every stamp's digest
max_attempts: <int>            # TOTAL generation attempts shared across both feedback edges (>= 1)
archive: <relative/template>   # optional; default ".claude/sdd/archive/specs/{name}/"
stages:
  - id: <unique-id>
    kind: create | lint | generate | judge | emit
    input_contract: <name>              # what this stage consumes
    output_contract: <name>             # what a create/generate stage produces
    judge_tier: smoke | standard | high-assurance    # judge stages only
    require_approval_for: [<class>, ...]              # emit stages only
```

`PipelineContract` (`spec_composer/contract.py`) implements the sibling Linter's `Contract` protocol — `name`, `parse`, `check` — so validating a contract is the exact call the Linter uses for any other artifact: `lint(document, PipelineContract())`, which is what `--check` runs (§5). `parse` stays permissive — it raises only when the top level is not a mapping — so `check` owns every rule below and the severity it fires at, and a defect is a named, gradeable finding rather than one opaque failure. Only a contract that does not FAIL is built into the strict, frozen `PipelineSpec` the engine actually runs against.

| Rule | Severity | Fires when |
|---|---|---|
| `pipeline-contract.unparseable` | FAIL | The document is not a mapping at the top level |
| `P1.missing_field` | FAIL | `pipeline`, `version`, or `stages` is absent or empty; a stage has no `id` |
| `P1.max_attempts` | FAIL | `max_attempts` is absent, a boolean, non-integer, or `< 1` |
| `P1.archive_template` | FAIL | `archive` is an absolute path, or contains a `..` segment that would leave the workspace |
| `P1.unknown_kind` | FAIL | A stage's `kind` is outside `create \| lint \| generate \| judge \| emit` |
| `P1.duplicate_stage_id` | FAIL | Two stages declare the same `id` |
| `P1.unknown_field` | WARN | An unrecognized top-level or stage key |
| `P2.judge_without_subject` | FAIL | A `judge` stage has no producing stage before it |
| `P2.judge_after_gates` | FAIL | A `judge` stage has no `lint` stage between its nearest preceding producer and itself |
| `P2.generate_gated` | FAIL | A `generate` stage has no `lint` stage between its nearest preceding `create` and itself |
| `P2.emit_gated` | FAIL | An `emit` stage has no producing stage before it, or no `lint` stage between that producer and itself |
| `P2.emit_last` | FAIL | An `emit` stage is not the final stage in `stages` |
| `P3.stage_io_chain` | FAIL | A stage's `input_contract` names something no upstream stage produced |
| `P3.judge_tier` | FAIL | A `judge` stage omits `judge_tier`, or names one outside the three known tiers |
| `P3.dangling_reference` | WARN | A referenced contract name is not among the contract's known bindings |

The `P2.*` ordering rules are subject-aware, not positional: each stage is checked against the producing stage whose output it actually consumes. This is what makes a pipeline with several `generate`/`judge` cycles before one final `emit` legal (`examples/multi_cycle.yaml`) while still rejecting a `judge` that runs before any gate has touched its subject (`examples/invalid_judge_before_gate.yaml`), an `emit` promoting something no gate ever saw (`examples/invalid_ungated_emit.yaml`), and an `emit` that is not the pipeline's last stage (`examples/invalid_emit_not_last.yaml`).

The one shipped pipeline, `pipelines/agent-creation.yaml`, is `create-spec` → `gate-a` (binds `creation-spec`) → `generate-agent` → `gate-b` (binds `agent-spec`) → `judge-agent` (`standard` tier) → `emit-agent`, with `max_attempts: 3`. Gate A and Gate B are this pipeline's own stage ids, not schema vocabulary — a different pipeline is free to name its gates anything. Gate B's `agent-spec` binding checks structural conformance only; what it does not yet catch is recorded in §8.

## 3. Verdict semantics (BINDING)

The Composer emits no verdict vocabulary of its own. Every `lint` and `judge` stage returns the same `Verdict` (`PASS | WARN | FAIL`) the sibling engines return, and the Composer records it unchanged in `ComposeResult.trail: tuple[StageVerdict, ...]`. **Consumers MUST NOT reinterpret FAIL.** A FAIL is the only verdict the conductor acts on: it routes the run back to the nearest preceding producing stage (§2); a PASS or WARN lets the walk continue, exactly as a WARN does for the sibling Linter and Judger.

A verdict is not the whole story a run tells, because a run can also stop for reasons that are not a judgment about the artifact at all — a stage waiting on a file the host has not written yet, an approval the operator has not granted, a sibling component that is unavailable. That second axis is the `Disposition` — `emitted | blocked | error | paused | waiting` — carried on `ComposeResult.disposition` and mapped to an exit code by the CLI (§5). `ComposeResult` also carries `stage` (where the run stopped), `epoch` and `attempt`/`attempts_spent` (§6), `artifact` (the promoted path, set only on `emitted`), and `expected_path` (what the host must produce next on `waiting`, or where promotion was headed on any other non-emitted disposition).

## 4. The seams: contracts, generation, evaluation (BINDING shape)

Three seams are injected into `compose()`, all keyword-only and all defaulting to a working binding: `compose(request, pipeline_contract, *, resolver=None, generator=None, evaluator=None)`. The conductor holds no model vocabulary and no generation logic of its own — it only dispatches to whichever concrete object each seam is given.

**`ContractResolver`.** A stage's `input_contract` / `output_contract` is a name, not an object. A resolver binds that name to a `spec_linter.Contract` via `resolve(name) -> Contract`, raising `UnresolvedContractError` when nothing is bound. `DefaultResolver` — used when no resolver is passed — binds `creation-spec` to `CreationSpecContract()` and `agent-spec` to `AgentSpecContract()`, both from the sibling `spec_linter`. An unresolvable name is a configuration defect, not a transient failure: it exits 2 (§5), because re-running cannot clear it.

**`Generator`.** `generate(request: GenerationRequest) -> GenerationOutcome` produces the output of a `create` **or** `generate` stage — one seam for both producing kinds, so spec creation and artifact generation are the same handoff. `GenerationRequest` carries the stage id and kind, the output path expected for this attempt, the input path and text, the current attempt number, and — on a routed-back attempt — the `feedback: tuple[Finding, ...]` that sent the run back here.

The shipped `StagedArtifactGenerator` does **not generate**. A deterministic conductor cannot invoke a host-side sub-agent in-process, so it only reports whether the expected file already exists at the requested path: if it does, the run proceeds; if not, the conductor turns that into `Disposition.WAITING` (exit 4, reason `awaiting-artifact`) and hands off. The intended production binding is a host-side generating sub-agent supplied through this same `Generator` seam — documented here, not hard-wired into the package, so the conductor stays deterministic and token-free regardless of what eventually implements generation. Until that binding lands, every consumer drives the identical staged handoff:

```bash
# 1. Ask the conductor to run the pipeline over a spec you already wrote
spec-compose specs/code-reviewer.spec.md --out .claude/agents/dev/code-reviewer.md
# -> DISPOSITION: WAITING (awaiting-artifact)   exit 4
#      expected at: .claude/storage/composer/agent-creation/code-reviewer-<digest>/staging/attempt-1/code-reviewer.md

# 2. The host (today, a human; eventually a generating sub-agent) writes exactly that file

# 3. Re-run the IDENTICAL command — every already-cleared stage skips on its stamps
spec-compose specs/code-reviewer.spec.md --out .claude/agents/dev/code-reviewer.md
# -> DISPOSITION: EMITTED   exit 0
#      emitted to: .claude/agents/dev/code-reviewer.md
```

If a later gate rejects what was written, the same loop repeats one stage later: the conductor reports `WAITING` again at a new `attempt-{n}` path, this time carrying the gate's findings as `feedback` so the regeneration can act on them (§6). `FakeGenerator(script)` (`spec_composer/generator.py`) is the offline stand-in the test suite uses — a `(request) -> str | None` callable that writes its return value to the requested path, or reports "not produced" by returning `None`.

**`Evaluator`.** The `judge` stage's evaluator is the sibling Judger's own `Evaluator` type — the Composer declares no type of its own and references it only under `TYPE_CHECKING`, so importing `spec_composer` never pulls in `spec_judge`. `spec_composer.judging.judge_artifact()` imports `spec_judge` **inside the call**: contract checking, a judge-less pipeline, and `--selfcheck` all work with the sibling absent. Every cause that keeps the judge stage from running — the sibling missing, or a budget, config, or network failure inside `spec_judge` — becomes `JudgeUnavailableError`, which the conductor turns into `Disposition.PAUSED` (exit 3, reason `judge-unavailable`). Unavailability is never read as a passing verdict.

## 5. I/O and the CLI (BINDING)

```text
spec-compose <spec> --out PATH [--pipeline PATH] [--approve CLASS]... [--json]
spec-compose --check <pipeline-contract-path>
spec-compose --selfcheck
```

`<spec>` is optional on a run: when the pipeline's `create` stage is responsible for producing it, omit it and the first `create` step reports `waiting` at the fixed path it expects (§4, §6). When supplied, the path must already exist — a spec path that does not resolve is an operator error (exit 2), not a handoff. `--pipeline` selects the pipeline contract to run (default: the shipped `pipelines/agent-creation.yaml`). `--json` renders the result as structured JSON instead of the human-readable trail; verdict levels render as names (`"PASS"`), never as a raw integer.

### `--check` vs. a run

`--check` validates a pipeline contract **without running it**, and is a different surface from a run: it follows the sibling Linter's own contract exactly — 0 PASS/WARN, 1 FAIL, 2 unloadable — because `--check` literally is `lint(document, PipelineContract())` (§2). "Unloadable" means the path could not be read at all — it does not exist, or it is a directory rather than a file. A document that *loads* but is not a pipeline contract (a YAML list, a scalar, an empty file) is a FAIL like any other, reported as `pipeline-contract.unparseable`, so authoring mistakes stay inside the verdict surface instead of escaping it as a process error. A run instead maps a `Disposition` to one of five codes (below), and a schema-invalid pipeline contract is one of the operational failures a run reports as `error`. **The same invalid contract therefore exits 1 under `--check` and 2 during a run.** That is a deliberate difference in what the two surfaces are answering — a verdict *about* the contract under `--check`, versus "the run could not start" during a run — not an inconsistency; it is called out explicitly here so it is never read as one.

### Exit codes

Any code >= 2 means no verdict was reached and must never be read as PASS.

| Code | Disposition | Meaning |
|---|---|---|
| 0 | emitted | Every declared stage cleared and the artifact was promoted |
| 1 | blocked | Budget exhausted on a gate FAIL, a high-assurance judge FAIL, a gate FAIL with no stage to route to, or a producer stalled at the progress ceiling (`no-progress`) — the only one of these four reached with no verdict at all |
| 2 | error | Operational failure — the run could not start, or could not complete for a reason that is not a verdict |
| 3 | paused | A bound stage could not run, or a required approval is outstanding. Never PASS |
| 4 | waiting | A producing stage has no usable output for this attempt; write it and re-run the identical command |

### Reasons

Every non-zero disposition carries a machine-readable `reason` from one closed vocabulary:

| Reason | Disposition | Meaning |
|---|---|---|
| `awaiting-artifact` | waiting | The expected output path does not exist yet |
| `stale-artifact` | waiting | A file exists at the expected path, but this stage already stamped that exact content before — in this epoch or any earlier one — so it cannot be accepted again as the new output. A second consecutive occurrence at the same stage escalates to `no-progress` instead of waiting again |
| `no-progress` | blocked | The same stage's second `stale-artifact` occurrence within one epoch: it was presented the same already-stamped bytes again, with nothing new in between, so the run stops instead of waiting again for information that cannot arrive. The budget is deliberately not charged — this is a stall, not a spent generation attempt |
| `approval-outstanding:<class>` | paused | `require_approval_for` names a class that has not been granted |
| `judge-unavailable` | paused | The sibling Judger is absent, or a credential, budget, or network failure kept it from running |
| `target-modified` | paused | The emit target holds bytes no emit stamp certifies and that are not the staged bytes either — it was edited in place, or it belongs to something else. Nothing is written; move the target aside (or delete it) and re-run to promote |
| `budget-exhausted` | blocked | A gate FAIL when spending one more generation attempt would meet or exceed `max_attempts` |
| `no-feedback-target` | blocked | A gate FAIL with no producing stage before it to route to. Defensive: `P2.emit_gated` / `P2.judge_after_gates` make a gate with no upstream producer un-`--check`-able, so a contract that passes `--check` cannot reach it |
| `high-assurance-judge-fail` | blocked | A blocking behavioral verdict at the `high-assurance` tier, pending human review |
| `judge-unparseable` | error | The judge stage's subject could not be structurally parsed. Classified before the tier is consulted, at every tier: "could not be read" is an operational failure, never a behavioral verdict awaiting a human. It is also the only way a judge FAIL can occur below `high-assurance`, since `smoke`/`standard` are WARN-capped by construction |
| `promotion-failed` | error | The emit target could not be replaced; it is left byte-identical to its pre-run state |
| `archive-failed` | *(event only — disposition stays `emitted`)* | The provenance write failed after a successful promotion |

`archive-failed` never changes the disposition: the artifact was already promoted, and reporting anything but `emitted` would misstate what happened.

### Pre-run reasons

A failure **before** the first stage runs has no disposition of its own — nothing was appended to the evidence log, so there is nothing to resume from. Under `--json` it is still rendered as one object of the same shape (`disposition`, `reason`, `detail`), so a host parses one surface either way. Every such failure exits 2, except a judge that could not run, which exits 3 and reuses `judge-unavailable`.

| Reason | Meaning |
|---|---|
| `contract-unloadable` | The pipeline contract path does not exist, is a directory, or is not readable YAML |
| `contract-invalid` | The pipeline contract loaded but FAILs its own check — the same document exits 1 under `--check` |
| `linter-absent` | The required sibling `spec_linter` could not be imported |
| `out-required` | A run was requested without `--out` |
| `spec-not-found` | The supplied spec path does not exist |
| `run-failed` | An exception escaped `compose()` — an unresolvable contract reference, an invalid archive template, or an unexpected error. `detail` carries the cause |

### `--approve`

An `emit` stage may declare `require_approval_for: [<class>, ...]` in the pipeline contract — policy the contract owns. Granting a class is operator input, supplied with a repeatable `--approve CLASS` flag; it can only satisfy a class the contract already requires, never add or remove one. A grant is appended to `run.jsonl` as an `approval` row and replayed on every later run in the same epoch, so it persists across re-runs exactly as a stamp does:

```bash
spec-compose specs/tool.spec.md --out .claude/agents/dev/tool.md
# -> DISPOSITION: PAUSED (approval-outstanding:publish)   exit 3

spec-compose specs/tool.spec.md --out .claude/agents/dev/tool.md --approve publish
# -> DISPOSITION: EMITTED   exit 0
```

`--tier` and `--max-attempts` do not exist as flags, deliberately: both are pipeline-contract policy (`judge_tier` per stage, `max_attempts` at the top level), and a call-site override would let an invocation quietly relocate policy out of the contract that is supposed to own it. A consumer who wants a different tier or budget edits the contract.

### `--selfcheck`

Reports whether the sibling `spec_linter` resolves (required — exit 2 when it does not) and whether `spec_judge` resolves (optional — reported either way, always exit 0). Useful as a CI or install-time smoke check, independent of running any pipeline.

### Programmatic use

`from spec_composer import compose` (bound lazily on first access, so importing the package never requires `spec_judge` to be installed); `from spec_composer.contract import PipelineSpec`. Pass any `ContractResolver` / `Generator` / `Evaluator` to run against fakes, exactly as the Judger's own tests inject a fake evaluator.

## 6. Run state, resume and the archive (BINDING)

### Identity and evidence

Every run is identified by its pipeline name and the resolved emit target path — `.claude/storage/composer/{pipeline}/{stem}-{sha256(resolved target)[:12]}/` under the workspace root (the nearest ancestor directory holding a `.claude/` folder) — so two pipelines writing different targets never share evidence or a budget. When no ancestor holds a `.claude/` directory there is no workspace to find, and **the current working directory becomes the workspace root**: run state and the archive land under the directory the command was issued from. That is a deliberate fallback rather than an error — a run outside a workspace still works, and still keeps its evidence — but it means the same command issued from two different directories is two different runs. `COMPOSER_RUN_ROOT` overrides this root outright. `SPEC_COMPOSER_PYTHON` selects the interpreter the `spec-compose` wrapper prefers, ahead of a local `.venv` and the ambient `python3`/`python`.

Everything that happens is one line of JSON appended to `run.jsonl` inside that directory — never rewritten, only appended, and fsynced after every write. A crashed or killed process loses nothing but the write it was in the middle of; a torn trailing line is discarded on the next read rather than crashing the run. Five row kinds carry the whole story: `stamp` (a stage cleared this content under this rule), `spend` (a gate FAIL charged to the shared budget, carrying its derived routing target and findings), `approval` (classes an operator granted), `run-closed` (a terminal disposition, which opens the next epoch), and `event` (a pause, a wait, or a recorded operational failure such as `archive-failed`).

### Resume

Every run **folds** `run.jsonl` from scratch before it does anything else — there is no in-memory state carried between invocations. The fold produces the current epoch (one plus the number of `run-closed` rows), `attempts_spent` (the number of `spend` rows since the last `run-closed`), the granted approvals, and every stamp. A stage is skipped when a **PASS or WARN** stamp already certifies its current subject: a `lint` stage compares its input against the stamp, a producing (`create`/`generate`) stage compares its input and then re-reads the payload path **its own stamp recorded**, and an `emit` stage skips only when the target already holds **exactly the bytes this run would promote** and some emit stamp certifies them — both, because a stamp says the target was promoted at some point, not that it matches the artifact standing behind this run — so re-running the identical command after an interruption simply resumes from the first stage whose evidence no longer matches what is on disk now. A verdict that is anything else — FAIL, or a token from no known vocabulary — certifies nothing, so a torn or hand-edited log makes its stage re-run rather than silently clearing it.

Resolving a producing stage's payload from its stamp rather than from the current attempt number is what makes a finished stage stay finished: an artifact that passed on the third attempt is still the artifact the run stands behind on the next invocation, even though a fresh epoch numbers its attempts from one again.

A new epoch resets the budget; it never resets the **evidence**. Freshness — the rule that stops a stage from re-presenting content it has already stamped — is judged against every stamp in the log, not only the current epoch's. Without that, closing a run would make every already-judged artifact look new again, and the next invocation would walk the whole repair loop a second time to re-reach verdicts already recorded.

`max_attempts` is the **total** number of generation attempts allowed per artifact — one initial attempt plus up to `max_attempts - 1` repairs — one budget shared across **both** feedback edges (a Gate A FAIL routes back to `create`; a Gate B FAIL routes back to `generate`). The budget is checked at the moment of a gate FAIL, before any route is recorded: if spending one more generation attempt would meet or exceed `max_attempts`, no further repair is recorded at all — the run ends `blocked` with reason `budget-exhausted` instead. Exhaustion escalates to a human; the conductor never retries past it or silently passes. A terminal `emitted` or `blocked` disposition appends a `run-closed` row and opens a new epoch, so a fixed problem gets a full budget again on the next run — `blocked` ends the run, never the artifact, permanently.

A second, independent bound guards against a different failure mode: a stage that keeps being presented byte-identical content a gate already rejected. `is_fresh` refuses to accept that content again (above), which turns it into a `stale-artifact` wait rather than a silent skip. The first such wait at a stage, within the current epoch, is free — a host may re-run the identical command before it has regenerated anything at all. A second occurrence at the *same* stage means the stage was presented the same already-stamped bytes again, with nothing new in between: the run stops `blocked` with reason `no-progress` instead of waiting again for information that cannot arrive. This ceiling (`STALE_WAIT_CEILING = 2` in `engine.py`) is a stage-scoped count within the current epoch, reset the moment that stage stamps fresh content, and it is never charged to `attempts_spent` — no generation attempt was spent on a stall.

Staged output is scoped by attempt **and** by stage: `staging/attempt-{n}/{stage-id}/{basename}`. Two producing stages in one pipeline therefore never write to the same file, so neither can overwrite the artifact a gate already cleared for the other.

A new epoch may **overwrite** `staging/attempt-{n}/` left behind by a previous epoch: the run directory is disposable working state, not an archive, and it is excluded from version control. Deleting it is always safe — the next run simply re-pays at most one generation.

### The archive and the canonical-frontmatter rule

On a successful emit, the conductor also writes the ephemeral creation spec — **verbatim** — plus a `provenance.json` (pipeline id and version, epoch, attempts spent, per-stage digests, the resolved target path, a timestamp) to `.claude/sdd/archive/specs/{name}/` (the contract's `archive:` template, which must be relative and resolve inside the workspace or the run ends in error before any stage runs). Unlike the run directory, the archive **is** committed — it is provenance the repository keeps.

**After emission, the artifact's own frontmatter is the canonical spec.** The archived copy is a build record — provenance only, describing how the artifact came to exist and under what rules — and no code path in this package ever reads it back to operate. Nothing about any later run depends on the archive's contents; deleting it changes no runtime behavior. An archive write that fails **after** a successful promotion is logged (an `event` row, reason `archive-failed`) but does not change the disposition — the artifact is already `emitted`, and reporting anything else would misstate what happened.

A regenerated artifact therefore reaches the target: once a spec edit invalidates the old build and a new artifact clears the gates, the emit stage runs again, promotes it, stamps it and refreshes `provenance.json` for that target. Reporting `emitted` while the previous version stayed in place would make the disposition a claim the file does not support.

That canonical status is enforced at the emit boundary, not merely asserted. If the target exists and holds bytes that **no** emit stamp certifies and that are not the staged bytes either, it was edited in place after the last promotion (or it belongs to something else entirely): the run stops at `paused` / `target-modified` and writes nothing. To promote over it deliberately, move the edited file aside or delete it, then re-run — the conductor never resolves that conflict on the operator's behalf.

The archive directory is keyed by the artifact **name**, so two artifacts sharing a name resolve to one archive. Names must therefore be **unique across everything a workspace archives**, exactly as the artifacts themselves are. A second artifact archiving under a name already recorded for a different target is refused rather than overwritten, and the refusal surfaces as `archive-failed` — provenance is never silently replaced.

## 7. Usage patterns (SUGGESTIONS — consumers choose)

- **Host loop around exit 4 and exit 3.** Drive the conductor from a host session: on `waiting`, produce the reported file and re-run the identical command; on `paused`, clear the cause (grant the approval, or wait out a transient judge outage) and re-run; on `blocked`, stop and escalate to a human either way — a budget was spent on a gate FAIL or a high-assurance judge FAIL worth a person's attention, or the producer stalled at the progress ceiling (`no-progress`) with the budget untouched but no path forward without a person looking at it.
- **`--check` at authoring time.** Validate a new or edited pipeline contract before it is ever run, in CI or locally — `P3.dangling_reference` in particular is useful only here, since it warns about a name that would only fail at run time.
- **`--selfcheck` as an install or CI smoke test.** Confirms the sibling Linter resolves (required) and reports whether the Judger does (optional), independent of running any pipeline.
- **A judge-less pipeline for a cheap loop.** Drop the `judge` stage entirely for a fast create/gate/generate/gate/emit cycle when behavioral review is not warranted for every artifact; the ordering rules accept it, since `judge` is not mandatory, only correctly placed when present.
- **A new artifact type is a new pipeline plus a new resolver binding.** The engine has no vocabulary for "agent" or "spec" — extending the Composer to another artifact type costs a YAML file and, if new contract names are needed, an entry in a `ContractResolver`'s bindings. No engine change.

These are patterns, not requirements. The engine does not mandate any of them.

## 8. Status & scope

Prototype: one engine, one concrete shipped pipeline (agent creation). It orchestrates artifact creation inside a developer session — there is no macro layer sequencing multiple pipelines, no durable execution journal beyond the append-only stamp log, and no concurrency control across simultaneous runs on the same target.

**Gate B's known gap.** Gate B currently binds the `agent-spec` contract, which checks structural conformance only. It cannot yet catch an artifact that is structurally valid but missing sections a given assurance tier requires. That check is intended to land as a *second* `lint` stage bound to a tier-required-sections contract by name — a few lines of YAML plus one resolver binding, no engine change — once that contract exists. Until then, a tier-incomplete-but-structurally-valid artifact can clear Gate B.

**No CLI overrides for policy.** `--tier` and `--max-attempts` are deliberately absent (§5) — both are contract fields, not run-time choices, so a consumer who wants a different tier or budget edits the pipeline contract rather than passing a flag.

**The production generator binding is documented, not shipped.** §4 describes the intended host-side generating sub-agent binding; the shipped default (`StagedArtifactGenerator`) only detects a file's presence and hands off. Until a generator binding is wired at the call site, every run of the shipped pipeline needs a human or host loop on the other end of the exit-4 handoff.

Not built yet: mid-stage resume (a run restarts a stage from scratch, never partway through it), locking against concurrent runs on the same target, budget variation by artifact type, and any distribution, signing, or trust step past `emit`.
