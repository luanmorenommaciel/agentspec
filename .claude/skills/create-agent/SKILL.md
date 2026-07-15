---
name: create-agent
description: |
  Repo-specific SOP for adding a new agent to this repository — the frontmatter
  contract the auto-generated router feeds on (name, description one-liner, tier,
  model, tools, kb_domains, stop conditions, escalation targets), the thin-executor
  default, category placement, and the router/build/docs ship checklist. Use when
  the user wants to create an agent, add a new agent to this repository, or asks
  for a new specialist agent. Do not use for creating skills (use create-skill) or
  KB domains (use /create-kb); to decide whether an agent is even the right layer,
  run the component-model skill first — most "new agent" requests turn out to be
  new skills plus a thin executor.
---

# Create an Agent (repo conventions)

Agents are the EXECUTION layer of the component model: identity, tool scope, model tier, stop conditions, escalation — a thin shell around capabilities. The scaffold and tier rules are owned by `.claude/agents/_template.md`; the layer decision is owned by the component model. This skill carries the repo mechanics between those two: the frontmatter contract as the router reads it, the thin-executor default, and the checklist an agent passes before it ships.

## Division of labor

| Concern | Owner |
|---|---|
| Is an agent even the right layer? | the `component-model` skill (gate), grounded in `.claude/kb/shared/component-model.md` |
| Section structure, tier line budgets, section-by-tier requirements | `.claude/agents/_template.md` (copy it) + `.claude/agents/README.md` |
| The methodology the agent executes | a skill, authored via `create-skill` |
| Frontmatter contract, router coupling, ship checklist | this skill |

## When to use / Skip if

**First, run the layer gate.** Before writing anything, apply the `component-model` skill (or read `.claude/kb/shared/component-model.md`). Most "new agent" asks are actually new skills plus a thin executor: if the request is "teach the system HOW to do X", that is a skill — the agent, if one is needed at all, is only the WHO (identity, tools, boundaries).

Use this skill when:

- Adding a new specialist agent under `.claude/agents/`.
- Splitting an overloaded agent into two roles with distinct tool scopes or KB domains.

Skip if:

- The capability is methodology or how-to knowledge → `create-skill`.
- The content is reference truth (facts, standards, deep dives) → `/create-kb`.
- An existing agent already covers most of the capability → extend it instead; apply the four-condition gate in `.claude/agents/README.md` ("When NOT to Create an Agent" — no existing agent covers >60%, unique KB/tool combination, ≥3 distinct triggers, no >80% overlap).
- Undecided which layer the logic belongs in → the `component-model` skill first.

## The agent contract (frontmatter)

The frontmatter is machine-read, not decoration. `scripts/generate-agent-router.py` regenerates the `agent-router` skill (SKILL.md + routing.json) from every agent's frontmatter — it extracts `name`, `tier`, `model`, the **first line** of `description`, `kb_domains`, and every `escalation_rules` `target:`. Write these as routing signals.

| Field | Required | Contract |
|---|---|---|
| `name` | all tiers | Kebab-case, matches the filename, `{tech\|domain}-{role}` style: `dbt-specialist`, `code-cleaner`, `fabric-architect`. |
| `description` | all tiers | Literal block (`\|`). The first line is extracted verbatim as the agent's routing one-liner — write it as the routing sentence, not a teaser. Second line: `Use PROACTIVELY when {triggers}.` Then two example blocks per house convention (Context / user / assistant). |
| `tier` | all tiers | `T1` utility (80-150 lines) / `T2` domain expert (150-350) / `T3` platform specialist (350-600). Governs which template sections are required — see the tier guide comment in `_template.md`. |
| `model` | optional | Defaults to `sonnet`. Pick the cheapest tier that does the job: `haiku` for fast pattern work, `sonnet` for most agents, `opus` only where the judgment is genuinely complex. |
| `tools` | all tiers | Least privilege — scope to what the role needs. A read-only analyst gets no `Write`/`Edit`; grant `Bash` only if the role runs commands; include `Task` only for delegating agents (the build-phase executor is the precedent). |
| `kb_domains` | all tiers | Domains this agent reads. Every entry must exist in `.claude/kb/_index.yaml`; use `[]` if none. Feeds the router's KB-domain reverse index. |
| `color` | all tiers | One of blue, green, orange, purple, red, yellow. |
| `anti_pattern_refs` | all tiers | `[shared-anti-patterns]` → `.claude/kb/shared/anti-patterns.md`. |
| `stop_conditions` | T2+ | Conditions that make the agent halt or refuse and return control. |
| `escalation_rules` | T2+ | trigger / target / reason entries. Every `target:` must be a real agent `name` (or `user`) — the router builds the handoff graph from these, so a typo is a broken route. |
| `mcp_servers` | T3 optional | name / tools / purpose per server dependency. |

### Parser pitfalls

The router's parser is line-based, not a full YAML load. Silent failure modes:

- `kb_domains` must be the inline form `[a, b]` — a block-style YAML list is ignored, and the agent ships with no domains in the router.
- Escalation targets are read only from `target:` lines inside the `escalation_rules:` block, and must be lowercase kebab-case.
- `name`, `tier`, `model` must be single-line scalars; `description` must be a literal block (`|`) or a single line.
- The one-liner extractor takes the first non-blank description line and stops at example markers (`Example`, `**Example`, `-`, `Context`, `user:`, `assistant:`) — keep line one clean, complete, and self-contained.

### Worked example (thin T2 specialist)

```yaml
---
name: duckdb-specialist
description: |
  DuckDB specialist for local analytics, larger-than-memory queries, and Parquet-first pipelines.
  Use PROACTIVELY when users work with DuckDB, .duckdb files, or local OLAP queries.

  Example 1 — User wants warehouse-free analytics:
  user: "Query these Parquet files without spinning up a warehouse"
  assistant: "I'll use the duckdb-specialist agent to build the DuckDB query."

  Example 2 — User hits a memory limit:
  user: "My DuckDB aggregation runs out of memory"
  assistant: "Let me invoke the duckdb-specialist to configure spilling and rewrite the query."

tier: T2
model: sonnet
tools: [Read, Write, Edit, Grep, Glob, Bash, TodoWrite]
kb_domains: [modern-stack]
anti_pattern_refs: [shared-anti-patterns]
color: yellow
stop_conditions:
  - Query validated against sample data, results returned
  - Task requires a distributed engine — out of scope
escalation_rules:
  - trigger: Workload outgrows a single machine
    target: spark-engineer
    reason: Distributed processing is the Spark lane
---
```

From this contract the router derives: the one-liner (description line one), a `modern-stack` reverse-index entry, and a `duckdb-specialist` → `spark-engineer` edge in the handoff graph.

## Thin executor by default

New agents start thin: the frontmatter contract, an identity statement, the role's non-negotiable policies, and one loading instruction — *read the corresponding skill and execute it*. Write the methodology as a skill via `create-skill`, so it can be versioned, swapped, and reused by commands without touching the executor.

The SDD workflow agents (`.claude/agents/workflow/`) are the reference shape for this split — phase executors whose method lives in the workflow skills, per the component model.

A fat body — methodology written inline — is the exception and needs a stated reason (for example: the method is inseparable from the role's tool scope and nothing else will ever reuse it). "It was faster to inline" is not a reason; it is the first anti-pattern in `.claude/kb/shared/component-model.md`.

## Ship checklist

Every new agent passes this before review:

| # | Check | How |
|---|---|---|
| 1 | Scaffold from the template | Copy `.claude/agents/_template.md` into the right category folder — `architect/`, `cloud/`, `data-engineering/`, `dev/`, `platform/`, `python/`, `test/`, or `workflow/` (the directory becomes the router category). Keep only the sections your tier requires. |
| 2 | Frontmatter contract complete | All required fields for the tier; description first line = the router one-liner; `kb_domains` all exist in `.claude/kb/_index.yaml`; every escalation `target:` is a real agent name. |
| 3 | Regenerate the router | `python3 scripts/generate-agent-router.py` — CI runs it with `--check` and fails on drift, so never hand-edit the `agent-router` skill. |
| 4 | Rebuild the plugin mirror | Run `./build-plugin.sh` and commit the regenerated `plugin/` tree together with the agent (agents ship wholesale; the build strips `_template.md`). |
| 5 | Update the hand-maintained catalog | Add the agent to `.claude/agents/README.md` — category table, tier distribution, escalation map if it escalates — and to the docs reference tables (`docs/reference/README.md`). |
| 6 | Agent count references | If the total changes, update the counts in `CLAUDE.md`, `README.md`, `docs/README.md`, `plugin/README.md`, and `.claude/agents/README.md`. |
| 7 | CHANGELOG | Entry under `[Unreleased]` in `CHANGELOG.md`. |

## References

- `.claude/kb/shared/component-model.md` — the four-layer model, thin-executor pattern, anti-patterns (the `component-model` skill is its operational gate)
- `.claude/agents/_template.md` — the scaffold: frontmatter schema, tier guide, section-by-tier requirements
- `.claude/agents/README.md` — the hand-maintained catalog: categories, tiers, escalation map, "When NOT to Create an Agent"
- `.claude/skills/create-skill/SKILL.md` — the sibling SOP for the skill that carries the new agent's methodology
- `scripts/generate-agent-router.py` — the generator this frontmatter contract feeds
