# spec-composer

A deterministic, token-free **conductor** for artifact creation — the orchestration counterpart to the structural `spec-linter` and the behavioral `spec-judge`. It drives one artifact through a declared `create → gate → generate → gate → judge → emit` lifecycle expressed as data (a **pipeline contract**), and it spends no tokens itself: every model call and every artifact-producing step happens behind a seam it receives, not one it implements.

It reuses the sibling `spec-linter`'s `Verdict` / `Finding` / `Level` and its `lint` engine — the pipeline contract IS a Linter contract, so `spec-compose --check` is literally `lint(document, PipelineContract())`. The sibling `spec-judge` is optional and imported lazily: a judge-less pipeline, `--check`, and `--selfcheck` all work with it absent.

See [`USAGE.md`](./USAGE.md) for the full operator reference — the five exit codes, the closed reason vocabulary, the staged generation handoff, and the resume/archive rules.

## Design in one screen

- **Entry point** — `compose(request, pipeline, *, resolver=None, generator=None, evaluator=None) -> ComposeResult`, keyword-only seams that each default to a working binding, mirroring the Judger's `judge(artifact, contract, panel=None)`.
- **The lifecycle is policy, not code** — an ordered, typed stage list in a pipeline contract; a contract that violates the ordering invariant FAILs its own check rather than being silently accepted (rule table below).
- **Three injected seams, one per non-deterministic concern** — `ContractResolver` binds a stage's contract *name* to a Linter contract object; `Generator` produces a `create`/`generate` stage's output (the shipped binding does not generate — it reports whether the expected file exists and hands off; see `USAGE.md` §4); the Judger's own `Evaluator` runs a `judge` stage, referenced only under `TYPE_CHECKING` so the sibling stays optional.
- **Evidence, not memory** — one append-only, fsynced `run.jsonl` per (pipeline, target). Every run folds it from scratch, so a crashed or killed run resumes by re-running the identical command, skipping whatever a matching stamp already certifies.
- **A shared, total attempt budget** — `max_attempts` counts generation attempts, not repairs, across both feedback edges (a Gate A failure re-creates the spec, a Gate B failure regenerates the artifact); exhaustion escalates to a human rather than looping silently.
- **Fail-closed emission** — the emit target is only ever replaced by an atomic rename staged beside it; a promotion that cannot complete leaves the target byte-identical to its pre-run state.

## Lifecycle

```text
create ──▶ gate ──▶ generate ──▶ gate ──▶ judge ──▶ emit + archive
  ▲ Gate A FAIL ─────┘  ▲ Gate B FAIL ──────┘           │
  └──────── route to the nearest preceding producing stage ──────┘
            (one shared budget; exhaustion escalates to blocked)
```

Each `gate` is a `lint` stage — a `spec_linter.Contract` bound to what the previous producing stage wrote. A `judge` stage always sits downstream of a gate on its own subject: the ordering rules are subject-aware, so several generate/judge cycles can precede one `emit`, and `emit` is always the pipeline's last stage.

## Modules

| Module | Role |
|---|---|
| `spec_composer.engine` | The conductor — `compose()`, `RunContext`, the per-kind dispatch, stamping, routing, and budget accounting |
| `spec_composer.contract` | `PipelineDocument` (permissive), `PipelineContract` (a Linter `Contract` owning every rule below), `PipelineSpec` (the strict run-time view), `bound_contract_name` |
| `spec_composer.models` | Frozen value objects — `Disposition`, `ComposeRequest`, `GenerationRequest`, `GenerationOutcome`, `StageVerdict`, `StageRecord`, `ComposeResult`. Verdict tokens are imported from `spec_linter`, never re-declared |
| `spec_composer.protocol` | The two Composer-owned structural seams — `ContractResolver`, `Generator` |
| `spec_composer.resolver` | `DefaultResolver` — the shipped name-to-contract bindings (`creation-spec`, `agent-spec`) — and `UnresolvedContract` |
| `spec_composer.generator` | `StagedArtifactGenerator` (the shipped handoff) and `FakeGenerator(script)` for offline tests |
| `spec_composer.judging` | `judge_artifact()` — imports `spec_judge` inside the call; every could-not-run cause becomes `JudgeUnavailable` |
| `spec_composer.runstate` | Workspace-root resolution, run identity, the two digests, and `RunLog` (append + fold) |
| `spec_composer.emit` | `promote()` (atomic, fail-closed) and `archive_spec()` (provenance only, never read back) |
| `spec_composer.cli` | `main(argv) -> int` — the run / `--check` / `--selfcheck` modes and the five-code exit map |
| `spec-compose` | The Bash entry point — fails loudly without the sibling Linter, adds the Judger to `PYTHONPATH` only when present |

## Pipeline-contract rules

`PipelineContract` implements the Linter's `Contract` protocol (`name` / `parse` / `check`), so validating a pipeline contract runs through the exact same engine as any other artifact.

| Rule | Severity | Fires when |
|---|---|---|
| `pipeline-contract.unparseable` | FAIL | The document is not a mapping at the top level |
| `P1.missing_field` | FAIL | `pipeline`, `version`, or `stages` is absent or empty; a stage has no `id` |
| `P1.max_attempts` | FAIL | `max_attempts` is absent, a boolean, non-integer, or `< 1` |
| `P1.unknown_kind` | FAIL | A stage's `kind` is outside `create \| lint \| generate \| judge \| emit` |
| `P1.duplicate_stage_id` | FAIL | Two stages declare the same `id` |
| `P1.unknown_field` | WARN | An unrecognized top-level or stage key |
| `P2.judge_without_subject` | FAIL | A `judge` stage has no producing stage before it |
| `P2.judge_after_gates` | FAIL | A `judge` stage has no `lint` stage between its nearest preceding producer and itself |
| `P2.generate_gated` | FAIL | A `generate` stage has no `lint` stage between its nearest preceding `create` and itself |
| `P2.emit_gated` | FAIL | An `emit` stage has no producing stage before it, or no `lint` stage between that producer and itself |
| `P2.emit_last` | FAIL | An `emit` stage is not the final stage |
| `P3.stage_io_chain` | FAIL | A stage's `input_contract` names something no upstream stage produced |
| `P3.judge_tier` | FAIL | A `judge` stage omits `judge_tier`, or names one outside `smoke \| standard \| high-assurance` |
| `P3.dangling_reference` | WARN | A referenced contract name is not among the contract's known bindings |

The `P2.*` rules are subject-aware, not positional: each stage is checked against the producing stage whose output it actually consumes, so a multi-cycle pipeline is legal as long as every model-based stage still sits behind a gate on its own subject. `examples/multi_cycle.yaml` is a passing worked instance; `examples/invalid_judge_before_gate.yaml`, `examples/invalid_ungated_emit.yaml`, and `examples/invalid_emit_not_last.yaml` each trip exactly one rule above.

## Quickstart

```bash
# Validate a pipeline contract without running it
./spec-compose --check pipelines/agent-creation.yaml

# Run the shipped agent-creation pipeline over a spec you already wrote
./spec-compose specs/code-reviewer.spec.md --out .claude/agents/dev/code-reviewer.md

# Diagnostics
./spec-compose --selfcheck   # verify the sibling spec-linter (required) and spec-judge (optional) resolve
```

Real runs need the sibling `spec-linter` next to this package (`spec-judge` is optional — its absence pauses a bound `judge` stage rather than skipping it). Requires Python 3.12 with `pydantic` and `pyyaml`.

## Development

```bash
make spec-compose            # component test suite (offline, deterministic)
```

Every test runs with no provider credential, an isolated run root, and an isolated workspace, so the archive can never escape a temporary directory and no test can spend a real evaluation budget.
