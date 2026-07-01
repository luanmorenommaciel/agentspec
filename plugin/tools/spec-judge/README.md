# spec-judge

A model-based, contract-aware **behavioral** evaluation engine — the behavioral
counterpart to the deterministic `spec-linter`. The Linter asks *"is this well-formed?"*;
the Judger asks *"does this artifact **honor its contract**?"*, catching bodies that are
vague, self-contradictory, intent-drifted, or that never deliver a declared capability —
defects a structural check cannot see.

It returns the **same `Verdict`** (`PASS | WARN | FAIL`) the Linter returns, so a consumer
handles both gates with one code path. It reuses the sibling `spec-linter`'s value objects
by import.

## Design in one screen

- **Entry point** — `judge(artifact, contract, panel=None) -> Verdict`, mirroring
  `lint(artifact, contract)`. Pure orchestration: parse → run panel → consensus.
- **Two seams the Linter lacks** — a `BehavioralContract` (policy: what to probe) and an
  injected `Evaluator` (mechanism: the model call). Model I/O never lives in the contract.
- **Tiered adversarial panel** — `smoke` / `standard` / `high-assurance`, always with at
  least one fault-seeker. Advisory (`WARN`) by default; `FAIL` only at high-assurance under
  a strict three-way, cross-model consensus.
- **Bounded cost** — a shared per-day budget ledger, preflighted before a panel runs.

See [`USAGE.md`](./USAGE.md) for the full operator reference and
[`examples/calibration/`](./examples/calibration/) for one degraded fixture per category
plus a clean one.

## Quickstart

```bash
# Judge an artifact against a separate source spec
./spec-judge path/to/agent.md --spec path/to/spec.yaml --tier standard

# Or judge a self-contained agent.md whose frontmatter is its spec
./spec-judge path/to/agent.md --tier smoke

# Diagnostics
./spec-judge --selfcheck     # verify the sibling spec-linter resolves
./spec-judge --ledger        # today's budget usage
```

Real evaluations need `OPENROUTER_API_KEY`. Requires Python 3.12 with `pydantic` and
`pyyaml`, and the sibling `spec-linter` next to this package.

## Development

```bash
make spec-judge              # component test suite (offline, deterministic)
```

Every test runs on a deterministic `FakeEvaluator` — zero network, zero budget. The single
live test self-skips unless `OPENROUTER_API_KEY` is set.
