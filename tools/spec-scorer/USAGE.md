# spec-scorer — operator reference

## Invocation

```bash
./spec-score <path> [--kb-index PATH] [--explain]
```

- `<path>` — an agent spec: a `.yaml`/`.yml` mapping, or a `.md` file whose
  leading `---`-fenced YAML frontmatter IS the spec (same convention as the
  Linter).
- `--kb-index PATH` — a KB `_index.yaml`. Supplying it enables the
  `reference_integrity` dimension, which checks each declared `kb_domains` entry
  against the index's `domains:` mapping (plus `shared`).
- `--explain` — expand every dimension into its per-topic checkpoints, so the
  ratio is self-explanatory (see [Per-topic breakdown](#per-topic-breakdown---explain)).

The wrapper resolves an interpreter that can import `pydantic` and `pyyaml`
(honoring `$SPEC_SCORER_PYTHON`, then a local `.venv`, then ambient
`python3`/`python`) and puts the sibling `spec-linter` on `PYTHONPATH`. If the
sibling is missing, or no interpreter has the dependencies, it degrades **loudly**
(exit 2) rather than silently skipping.

## Exit-code contract

The Scorer is **analytical, not a gate** — there is no FAIL code. A low score is
a normal, successful result.

| Code | Meaning |
|---|---|
| `0` | SCORED — a ScoreCard was produced, whatever the scores are |
| `2` | ERROR — could not measure: missing/empty file, no frontmatter, non-mapping top level, an unparseable spec, or a bad `--kb-index` |

A consumer **never blocks on the exit code** — it reads the ScoreCard. Exit `2`
means *"could not measure"*, never *"measured badly"*. An artifact the Linter
`FAIL`s still scores at exit `0`, with its weaknesses localized in the card.

## Reading a ScoreCard

```
SCORECARD  (contract agent-spec 0.1.0, judger_tier=none, sources=artifact)
— Risk & Governance
  maturity_conformance   0.67  [2/3]
                        declared V2; missing: observability
```

- The ratio (`0.67`) is always shown with its **raw counts** (`[2/3]`) — the
  number never floats free of its evidence.
- `risk_surface` is annotated `(higher = more risk)`: it is a descriptor, not a
  defect. Read it paired with `mitigation_coverage`.
- The header records provenance. The contract's **name and version** together
  (`contract_version` alone cannot distinguish two contracts sharing a version)
  plus `judger_tier` are what let you refuse to compare a smoke-tier card with a
  high-assurance one, or cards scored against different contracts.

## Per-topic breakdown (`--explain`)

The compact card shows the ratio and a terse detail line. `--explain` expands
each dimension into the individual checkpoints behind the number, so a `3/4` is
never a mystery — you see exactly which topic failed and which passed.

```
$ ./spec-score agent.yaml --explain
— Platform Fit
  convention_conformance 0.75  [3/4]
    ✓ description_present
    ✓ description_is_one_liner
    ✓ tools_declared
    ✗ kb_domains_declared
— Risk & Governance
  risk_surface           0.17  [2/12]  (higher = more risk)
    +0  files_written (false)
    +0  git_operations (0 non-none)
    +0  external_apis (0)
    +1  tools (1)
    +1  tier (T2)
```

- **Boolean checks** render `✓`/`✗` — the topic either holds or it doesn't.
- **Weighted checks** render `+N` — the points that topic contributed, with the
  raw value in parentheses.
- The dimension's numerator reconciles with the breakdown: for the boolean
  checklists it is the count of `✓`; for `risk_surface` it is the sum of the
  `+N` (capped at 12).

Leave `--explain` off for corpus scans (the compact ratios stay scannable); turn
it on to debug or justify a single artifact's score.

### What each dimension checks

| Dimension | Checkpoints |
|---|---|
| `completeness` | one per enrichment field populated: `kb_domains`, `observability`, `memory_backend`, `recall_strategy`, `requirements`, `deliverables` |
| `reference_integrity` | one per declared `kb_domains` entry — resolves in the KB index or is `dangling` *(needs `--kb-index`)* |
| `convention_conformance` | `description_present` · `description_is_one_liner` (≤ 400 chars) · `tools_declared` (≥ 1) · `kb_domains_declared` (≥ 1) |
| `actual_reuse` | inbound reference count vs. a nominal target of 3 *(needs injected counts)* |
| `risk_surface` | `+1` files-written · `+1` per non-`none` git op · `+1` per external API · `+1` per tool · tier `T1=0 / T2=1 / T3=2`; cap 12 |
| `mitigation_coverage` | `stop_conditions` · `escalation_rules` · `observability` · `security_review` *(only when `publish: true`)* |
| `maturity_conformance` | evidence for the **declared** level — V1: `stop_conditions`, `escalation_rules`; V2: `+ observability`; V3: `+ memory_backend`, `recall_strategy` |
| `behavioral_cleanliness` | one per behavioral category absent: `B1.vagueness`, `B2.capability_not_delivered`, `B3.internal_contradiction`, `B4.intent_drift` *(needs a Judger verdict)* |

## Comparability — the discipline the metadata enforces

Two ScoreCards are comparable **only** when their `contract_version` and
`judger_tier` match. A smoke-tier judge run raises fewer categories than
high-assurance on the same artifact; a spec scored against a different contract
version is on a different scale. The metadata makes the mismatch visible — do not
average across it.

## Programmatic use

```python
from spec_scorer import score, AgentSpecScoringContract

card = score(spec_dict, AgentSpecScoringContract(known_kb_domains={"testing"}))
for family, dims in card.by_family().items():
    for d in dims:
        print(family, d.dimension, d.ratio, f"[{d.numerator}/{d.denominator}]")
        for item in d.checks:              # the per-topic checkpoints
            print("   ", item.label, item.contribution, item.note)

print(card.render(explain=True))           # the same breakdown, formatted
```

Fold behavioral evidence from a Judger verdict (accept-only — the Scorer never
invokes the Judger):

```python
card = score(spec_dict, AgentSpecScoringContract(), verdict=verdict, judger_tier="standard")
```

With no verdict, the Behavioral Quality family is **absent**, never zero — a
cheap run must never score better than no run.

## What V0 does not do

- No file-level convention checks (placement, size limits, thin-executor body
  length) — `convention_conformance` is the frontmatter-only subset.
- No repo-graph walk — `actual_reuse` takes injected inbound counts.
- No composite/overall score — by design (ADR-011 §3.6).
- No severity weighting of behavioral findings — a `Verdict` does not expose
  severity at the Scorer's boundary (every finding is `WARN` below the
  high-assurance tier), so `behavioral_cleanliness` measures **category
  presence**, which is also the signal most robust to panel size.
