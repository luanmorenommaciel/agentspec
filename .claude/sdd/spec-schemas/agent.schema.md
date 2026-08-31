# agent.schema.md — Spec Schema for Agent Creation

> Defines the ephemeral, pre-generation spec format for creating a new agent.
> Consumed by `agent-architect` (generation) and, going forward, by
> `tools/spec-linter/` (Gate A/B enforcement — see [Enforcement](#enforcement)
> below). Governed by ADR-006 (issue #67). Layer 1 of the `feat/spec-schemas`
> plan (issue #71).

## Naming note

This is **not** the same thing as `tools/spec-linter`'s `agent-spec` contract
(`spec_linter/contracts/agent_spec.py`, `spec_linter/models.py`'s
`AgentSpec`). That contract validates an *already-generated* `agent.md`
file's frontmatter as a structural artifact (L1 schema / L2 governance / L3
consistency). This schema instead defines the *creation-time* spec a human
fills in **before** `agent-architect` generates `agent.md` at all — the input
to the cube→square mapping below, not the output contract. The two will
likely need reconciling once Gate A/B enforcement lands (see Enforcement),
but that reconciliation is out of scope for Layer 1.

---

## Spec file location

Filled-in specs live at `.claude/sdd/specs/agents/{agent-name}.spec.md`
while in progress. Archival location: `.claude/sdd/archive/specs/{name}/`
(ADR-004 §3.9, resolving ADR-006 §7.1's deferral — provenance only, graduation
rule applies before archiving).

---

## Spec-only fields

These fields exist only in the spec. They inform generation and (eventually)
gate enforcement, but are never copied into the generated `agent.md`:

```yaml
intent: >
  # Why this agent is being created — one specific sentence.
  # Example: "No existing agent covers Snowflake-specific cost attribution
  # queries; data-platform-engineer's scope is too broad to specialize here."

success_criteria: >
  # What correct agent output looks like — feeds future Judger evaluation.

acceptance_tests:
  # Named test cases the generated agent must pass — feeds Gate B + Judger.
  - name: "{test case name}"
    scenario: "{input / trigger}"
    expected: "{expected behavior}"

overlap_check: 0.0   # Fraction (0.0-1.0) of scope covered by the nearest
                      # existing agent. Gate A input.

trigger_count: 0      # Number of distinct trigger scenarios declared below.
                       # Gate A input.

trigger_scenarios:
  - "{distinct scenario 1 that should invoke this agent}"
  - "{distinct scenario 2}"
  - "{distinct scenario 3}"
```

---

## Cube→square mapping

The spec is the "cube" (full-dimensional intent); `agent.md` is the
"square" (flattened, generated artifact). Two mapping modes:

**1:1 copy** — spec fields land in `agent.md` frontmatter unchanged:

```yaml
tier       → frontmatter.tier
model      → frontmatter.model
tools      → frontmatter.tools
kb_domains → frontmatter.kb_domains
```

**Generated, never copied** — `agent-architect` synthesizes these from spec
content; they must not appear as verbatim spec text in the output:

```yaml
name              ← derived from intent
description       ← generated from intent + trigger_scenarios
                     (including the <example> blocks _template.md requires)
stop_conditions   ← derived from spec constraints + acceptance_tests
escalation_rules  ← derived from spec constraints
```

If the mapping is ambiguous for a given spec (e.g. `intent` doesn't clearly
imply a `tier`, or `trigger_scenarios` don't cleanly separate from an
existing agent's scope), `agent-architect` stops and asks rather than
guessing — see its `stop_conditions`.

---

## Gate A / Gate B criteria

These are **documented here as the contract**, not enforced by
`agent-architect`. See [Enforcement](#enforcement).

**Gate A (pre-generation — should this agent exist at all):**

| Check | Threshold |
|---|---|
| `overlap_check` | < 0.60 |
| `trigger_count` | >= 3 |
| `intent` | non-empty and specific (not a restatement of the agent's name) |
| `tier` | one of `T1`, `T2`, `T3` |

**Gate B (post-generation — does the artifact honor the spec):**

| Check | Rule |
|---|---|
| Required sections | all `tier_requirements.{tier}.required_sections` from `_template.md` are present |
| Frontmatter fidelity | 1:1-mapped fields match the spec exactly; generated fields are not verbatim spec text |

---

## Enforcement

`agent-architect` (`.claude/agents/architect/agent-architect.md`) is scoped
to **generation only** — it does not self-check Gate A or Gate B. This is a
deliberate Layer 1 scope decision, not an oversight: gate enforcement is
`tools/spec-linter/`'s job (it already runs the `agent-spec` contract against
generated `agent.md` files today; extending it — or a sibling contract — to
check this schema's Gate A/B criteria against a spec file is a follow-up, not
part of Layer 1).

---

## Example (abbreviated)

```yaml
intent: >
  No existing agent covers dbt exposure lineage auditing; dbt-specialist's
  scope is model development, not cross-project exposure tracking.
success_criteria: >
  Given a dbt project, correctly maps every exposure to its upstream models
  and flags exposures pointing at deprecated/renamed models.
acceptance_tests:
  - name: "detects orphaned exposure"
    scenario: "exposure references a model removed from the DAG"
    expected: "flags the exposure with the missing model name"
overlap_check: 0.25
trigger_count: 3
trigger_scenarios:
  - "User asks to audit dbt exposure lineage"
  - "User asks which exposures break after a model rename"
  - "User asks for an exposure-to-model coverage report"
tier: T2
model: sonnet
tools: [Read, Grep, Glob, Bash, TodoWrite]
kb_domains: [dbt]
```
