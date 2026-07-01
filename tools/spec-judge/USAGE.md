# Spec Judge — Usage

The **Judger** is a model-based, contract-aware behavioral evaluation engine: the
behavioral counterpart to the deterministic Linter. Where the Linter asks *"is this
well-formed?"*, the Judger asks *"does this artifact **honor its contract**?"* — catching
vague, incoherent, intent-drifted, or capability-not-delivered bodies that are
well-formed and pass a general review.

## 1. What it is (BINDING)

One entry point, mirroring the Linter's `lint(artifact, contract)`:

```python
from spec_judge.engine import judge          # judge(artifact, contract, panel=None) -> Verdict
from spec_judge import SpecConformanceContract, Panel
```

`judge` returns the **same `Verdict`** the Linter returns (`from spec_linter import
Verdict, Finding, Level`), so a consumer handles both the structural and behavioral gates
with one code path. The engine parses the artifact via the contract, runs the injected
panel of evaluators, and folds their results into a verdict. It has no model vocabulary
and no I/O of its own — all of that lives behind the evaluator seam.

The Judger runs **only after the Linter passes** (a structural `FAIL` never escalates to
behavioral judgment) and inspects the **static artifact as written** — not live execution.

## 2. The contract and the evaluator seam (BINDING shape)

The Linter's `Contract` is `parse + check`, where `check` is pure. Behavioral evaluation
needs a model call, which must not live in the contract, so the responsibility splits into
two seams:

- **`BehavioralContract`** (`parse` + `rubric`) — policy. `SpecConformanceContract(spec)`
  binds the source spec as the contract: its `output_contract` + intent are what the
  artifact must honor.
- **`Evaluator`** (`evaluate`) — mechanism, injected. `OpenRouterEvaluator` is the real
  model call; `FakeEvaluator` is deterministic, for tests. The `panel` argument is the
  injection point.

`Panel(...)` defaults to the real `OpenRouterEvaluator` whenever no evaluator is passed in —
this is intentional (mirrors the Linter's `lint`), but it means tests should always inject
a fake explicitly rather than relying on an omitted argument to stay offline.

Findings are classified on four behavioral categories, analogous to the Linter's `L1–L4`:

| Rule | Meaning |
|------|---------|
| `B1.vagueness` | an instruction too vague to act on reliably |
| `B2.capability_not_delivered` | a declared capability the body never delivers |
| `B3.internal_contradiction` | instructions that conflict with each other or the contract |
| `B4.intent_drift` | coherent, but doing something other than the source spec asked |

## 3. Verdict semantics (BINDING)

| Verdict | Meaning |
|---------|---------|
| `PASS` | no behavioral concern — proceed |
| `WARN` | advisory behavioral concern — proceed, but record the finding |
| `FAIL` | critical behavioral deficiency — blocks; high-assurance tier only |

Behavioral judgment is probabilistic, so the engine is **calibrated to `WARN` by default**:
the smoke and standard tiers cap every finding at `WARN` (`FAIL` is unreachable there **by
construction**). `FAIL` is reserved for the high-assurance tier under a strict consensus
gate (§4). The `PASS | WARN | FAIL` tokens are identical to the Linter's, and the same rule
holds: **consumers MUST NOT reinterpret `FAIL`.**

Every seat's concerns become findings — a **union**, not a consolidation. When independent
voices converge on the same defect, each raises its own finding; that is corroboration, not
duplication, and it is not deduplicated away.

## 4. Independence tiers (BINDING)

Independence is dialed by stakes. One invariant holds in every tier: **at least one
fault-seeker** — a seat explicitly tasked to find where the artifact fails its contract.

| Tier | Panel | Verdict ceiling |
|------|-------|-----------------|
| `smoke` | 1 fault-seeker | `WARN` |
| `standard` (default) | fault-seeker + conformance-checker + arbiter | `WARN` |
| `high-assurance` | + a **cross-model** fault-seeker (different model), + arbiter | `FAIL`-eligible |

`FAIL` emits **only** at `high-assurance`, and only when the same-platform fault-seeker,
the cross-model fault-seeker, **and** the arbiter each independently raise a category at
high severity, and the weakest agreeing voice's confidence clears the floor (0.7). This
three-way, cross-model agreement is what makes a blocking verdict carry information.

The arbiter adjudicates peer concerns, but that adjudication only carries decision power
at this FAIL gate: a concern the arbiter declines to uphold still stays on record as an
advisory `WARN` finding from the reviewer who raised it. No single voice — not even the
arbiter — may silence the panel.

## 5. I/O and the CLI (BINDING)

```
spec-judge <artifact> [--spec SPEC] [--tier smoke|standard|high-assurance]
                      [--model M] [--alt-model M] [--json]
spec-judge --ledger       # show today's budget usage
spec-judge --selfcheck    # verify the sibling spec-linter resolves
```

`--spec` is the source spec (YAML). If omitted, the artifact's own YAML **frontmatter** is
used as its spec (the self-contained `agent.md` model); it is always stripped from the body
first, even when `--spec` is given, so the artifact's own frontmatter is never judged as
prose.

`--model`/`--alt-model` can also be set via `JUDGE_MODEL`/`JUDGE_ALT_MODEL` — an explicit
flag always wins over the environment variable. At `high-assurance`, the two must resolve
to different models: the CLI refuses (exit 2) rather than silently running all seats on
one model while still asserting cross-model agreement.

Exit codes — the **verdict** surface stays `PASS`/`WARN`/`FAIL` (codes 0/1). Codes 2/3/4
are *not* verdicts: they are "couldn't-run" states. A consumer treats any code `>= 2` as
"skip the behavioral check visibly and proceed" (never assume `PASS`), or branches:

| Code | Meaning |
|------|---------|
| `0` | `PASS` or `WARN` — proceed |
| `1` | `FAIL` — a high-assurance blocking verdict |
| `2` | ERROR — operational failure (missing/empty artifact, no spec, bad config) |
| `3` | BUDGET — the per-day evaluation budget is exhausted |
| `4` | NETWORK — model/API failure |

Programmatic use: `from spec_judge.engine import judge`.

## 6. Usage patterns (SUGGESTIONS — consumers choose)

- **post-lint evaluation** — run on a Linter `PASS`, at authoring checkpoints and before
  release. Never on a structural `FAIL`.
- **tier by stakes** — `smoke` in-loop, `standard` at a phase handoff, `high-assurance`
  pre-release.
- **two-pass refine** — feed `WARN` findings back into a regeneration, then re-judge.
- **opt-in blocking** — a consumer binding may act on a `high-assurance` `FAIL`; the default
  is advisory.

These are patterns, not requirements.

## 7. Cost & budget (BINDING-ish)

Every evaluation spends tokens. A shared, append-only per-day ledger caps spend across the
whole judge family (`JUDGE_BUDGET`, default 10 calls/UTC-day; `JUDGE_LEDGER` overrides the
path). The CLI **preflights** — it refuses to start a panel it cannot finish — and degrades
loudly (exit 3) rather than silently skipping. Set `OPENROUTER_API_KEY` for real calls.

The ledger is an **advisory** cost guard, not a hard quota or a security boundary: the
preflight check and the per-call backstop both read-then-write without locking, so
concurrent invocations racing the same ledger can each pass their own preflight and
together slightly overshoot the ceiling (bounded by one panel's worth of extra seats per
concurrent caller). This is an accepted, deliberate trade-off for a prototype — see §8.

Model selection (§5, `JUDGE_MODEL`/`JUDGE_ALT_MODEL`) and budget (`JUDGE_BUDGET`/
`JUDGE_LEDGER`) are independent knobs: the former picks which models run, the latter caps
how many calls run.

## 8. Status & scope

Prototype. It re-scopes the shipped V0 reviewer's cross-model mechanism and budget ledger
toward contract conformance; superseding that V0 is a separate migration. It judges the
static artifact against its contract — validating that the *contract itself* captures human
intent is out of scope (a human responsibility, tracked separately).

Explicitly open (calibration, not implementation): the confidence floor (§4), the WARN/FAIL
category rules, and the panel shapes are named, tunable knobs, not tuned ones. Two items are
still unresolved even in direction: **who owns and refreshes the calibration corpus** (the
`examples/calibration` fixtures are a starting set, not a maintained ground truth), and **what
run-to-run reproducibility target** a probabilistic evaluator should be held to (the same
artifact judged twice is not guaranteed to produce the same verdict).
