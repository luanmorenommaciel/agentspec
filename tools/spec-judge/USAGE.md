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

## 5. I/O and the CLI (BINDING)

```
spec-judge <artifact> [--spec SPEC] [--tier smoke|standard|high-assurance]
                      [--model M] [--alt-model M] [--json]
spec-judge --ledger       # show today's budget usage
spec-judge --selfcheck    # verify the sibling spec-linter resolves
```

`--spec` is the source spec (YAML). If omitted, the artifact's own YAML **frontmatter** is
used as its spec (the self-contained `agent.md` model).

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

## 8. Status & scope

Prototype. It re-scopes the shipped V0 reviewer's cross-model mechanism and budget ledger
toward contract conformance; superseding that V0 is a separate migration. It judges the
static artifact against its contract — validating that the *contract itself* captures human
intent is out of scope (a human responsibility, tracked separately).
