# spec-scorer

A deterministic, multi-dimensional **artifact scoring** engine — the analytical,
non-gating third member of the enforcement toolchain (ADR-011).

Where the **Linter** asks *"is this well-formed?"* and the **Judger** asks *"does
this honor its contract?"*, the **Scorer** asks *"how good is this artifact?"* —
and answers with measured per-dimension ratios, never a verdict. Two artifacts
that both `PASS` may still differ in completeness, platform fit, or declared risk;
the Scorer makes that difference visible.

## Design in one screen

- **Entry point** — `score(artifact, contract) -> ScoreCard`, mirroring
  `lint(artifact, contract)` and `judge(artifact, contract, panel)`. It takes the
  **artifact**, like its siblings — a fold over verdicts alone is blind to
  gradations that break no rule (an absent optional field yields zero findings
  whether 3 or 8 are filled).
- **Every metric is measured.** No model calls, no network, no budget — the
  Scorer is deterministic and free. Behavioral signal is *folded* from a Judger
  verdict, never re-judged. This is what keeps it from becoming a second Judger.
- **Analytical, never a gate.** Verdicts gate; scores inform. There is no FAIL
  exit code — a low score is a normal, successful result.
- **No composite score.** A single roll-up reintroduces the uninterpretable
  number the multi-dimensional design exists to avoid. Family roll-ups are
  possible only under caller-supplied weights (policy), never a built-in default.
- **Provenance travels with the score.** The `ScoreCard` carries `measured_at`,
  `contract_version`, `judger_tier`, and `evidence_sources` — the metadata that
  makes two ScoreCards detectably (non-)comparable.

## Dimensions (V0)

| Family | Dimension | Source | Emitted |
|---|---|---|---|
| Spec Quality | `completeness` | the spec | always |
| Spec Quality | `reference_integrity` | KB `_index.yaml` | with `--kb-index` |
| Platform Fit | `convention_conformance` | the spec | always |
| Platform Fit | `actual_reuse` | repo graph | with injected inbound refs |
| Risk & Governance | `risk_surface` | the spec | always (higher = more risk) |
| Risk & Governance | `mitigation_coverage` | the spec | always |
| Risk & Governance | `maturity_conformance` | the spec | always |
| Behavioral Quality | `behavioral_cleanliness` | a Judger `Verdict` | with a supplied verdict |

Dimensions whose evidence source was not supplied are **omitted, never zeroed**.
`maturity_conformance` is the one neither sibling can answer: does the artifact's
content support the maturity level it *declares*?

## Quickstart

```bash
# Score an agent spec (YAML mapping, or a .md whose frontmatter is the spec)
./spec-score path/to/agent.yaml

# Enable reference_integrity against a KB index
./spec-score path/to/agent.yaml --kb-index .claude/kb/_index.yaml
```

Requires Python 3.12 with `pydantic` and `pyyaml`, and the sibling `spec-linter`
next to this package (whose value objects it reuses by import).

## Development

```bash
make spec-scorer     # component test suite (offline, deterministic)
```

Every test runs offline with zero network and zero model calls — the Scorer has
no non-deterministic path to mock.

See [`USAGE.md`](./USAGE.md) for the operator reference and the exit-code contract.
