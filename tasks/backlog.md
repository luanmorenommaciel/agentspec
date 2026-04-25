# AgentSpec Backlog

> **Last Updated:** 2026-04-17
> **Current Version:** v3.1.0
> **Source of truth for pending work** — roadmap items tracked from strategic research and community feedback

---

## Legend

| Status | Meaning |
|--------|---------|
| 🟢 Done | Shipped and verified |
| 🟡 In Progress | Actively being built |
| 🔵 Ready | Spec complete, ready to build |
| ⚪ Planned | In roadmap, not yet specced |
| ⚫ Idea | Under consideration |

| Priority | Meaning |
|----------|---------|
| P0 | Critical — blocks other work |
| P1 | High — core feature for next release |
| P2 | Medium — improves quality of life |
| P3 | Low — nice to have |

---

## Recently Shipped (v3.1.0)

| Feature | Status | Notes |
|---------|--------|-------|
| Repo audit & dead reference fixes | 🟢 Done | 22 issues found, all fixed |
| New `supabase/` KB domain | 🟢 Done | 9 files, 4 concepts + 3 patterns |
| Lakeflow concepts (expectations, CDC, deployment) | 🟢 Done | Now at 5 concepts, in spec |
| AWS consolidated `quick-reference.md` | 🟢 Done | Lambda + Deployment combined |
| `agent-router` skill | 🟢 Done | Routing table for all 58 agents |
| `/status` command | 🟢 Done | Project health reporting |
| Stack auto-detection in init-workspace.sh | 🟢 Done | Detects 10+ tech stacks |
| CHANGELOG and count updates across repo | 🟢 Done | 22→23 KB, 29→30 commands |

---

## v3.2 — Medium Complexity (Next Release)

### 🟢 P1: Agent Router v2 — Phase 1 (Build-Time Generation)

**Description:** Replaced hand-maintained `agent-router` SKILL.md with build-time generation from agent frontmatter. Zero manual maintenance when agents are added, renamed, or retired — a single `python3 scripts/generate-agent-router.py` regenerates the routing tables.

**Shipped:**
- [x] `scripts/generate-agent-router.py` — parses frontmatter across all 58 agents, derives category/tier/model/kb_domains/escalations
- [x] Outputs `SKILL.md` (human-readable routing tables by category, KB domain reverse index, one-liners) + `routing.json` (machine-readable lookup for future semantic layer)
- [x] `--check` mode for CI: fails if on-disk files drift from generated output
- [x] Wired into `build-plugin.sh` as Step 0 (runs before plugin copy)
- [x] `DO NOT EDIT` header on generated SKILL.md pointing to the script
- [x] Content hash stamped into the file for drift detection

**Next phases (separate backlog items below):**
- Phase 2: Context-aware signals (branch, stack, session history) — v3.2
- Phase 3: Feedback loop via Memory Echo — v3.3
- Phase 4: Semantic index with `router.match` MCP tool — v3.3

---

### 🔵 P1: Flag System (Progressive Enhancement Framework)

**Description:** Unified flag vocabulary across all phase commands — preserves AgentSpec's simple surface while enabling opt-in depth (judges, autonomy, model overrides, parallel composition). Defaults reproduce today's behavior exactly; flags layer on power when requested.

**Philosophy:** Same dimmer-switch model as `git commit` → `git commit --amend --signoff -S`. Users never forced into complexity; opt in per run.

**Tasks:**
- [ ] Author `.claude/sdd/architecture/FLAGS.yaml` — single source of truth (namespace, type, values, default, applies_to, added_in)
- [ ] Write `scripts/parse-flags.py` — reusable flag resolver consumed by every phase command
- [ ] Write `scripts/generate-flag-docs.py` — emits `docs/reference/FLAGS.md` (same generator pattern as agent-router)
- [ ] Add flag handling section to `/brainstorm`, `/define`, `/design`, `/build`, `/ship` (read normalized config, pass to delegated agents)
- [ ] Ship first real flag: `--model=opus|sonnet|haiku` (trivial, proves pipeline)
- [ ] Wire `generate-flag-docs.py` into `build-plugin.sh` (Step 0b)
- [ ] Document flag namespaces: `--judge`, `--autonomous`, `--model`, `--depth`, `--evidence`, `--parallel`, `--budget`, `--format`
- [ ] Forward-compat rule: unknown flags → warn, don't error

**Future flags this unblocks (add as separate backlog items):**
- `--judge[=model]` — consumes Judge Layer (below)
- `--autonomous=safe|full` — consumes Overnight SubAgent
- `--parallel=a,b,c` — consumes Agents Composition
- `--evidence=fresh-only` — consumes KB Freshness
- `--memory=read|write|off` — consumes Memory Echo

**Why build this:** turns 15 future backlog items into **one grammar**. Every new capability becomes a flag, not a new command.

---

### 🟡 P1: Judge Layer via OpenRouter (V0 shipped, V1+ in flight)

**Description:** Cross-model verification — use OpenRouter (GPT, Gemini) to validate agent output against Claude's output. Detects hallucinations and bias that single-model judges miss.

**V0 Shipped:**
- [x] New `/judge <file>` standalone command — user opts in per invocation
- [x] `scripts/judge.py` — reads file, calls OpenRouter HTTP API with one model (default `openai/gpt-4o-mini`), returns PASS/FAIL + reasoning
- [x] `OPENROUTER_API_KEY` env var with clear error if missing
- [x] Hard per-day budget ceiling (10 calls default, `JUDGE_BUDGET` override) with append-only ledger at `.claude/storage/judge-ledger.jsonl`
- [x] Verdict format: markdown block with PASS/FAIL, confidence 0-1, severity-ranked concerns with evidence citations, suggested fixes
- [x] Distinct exit codes (0/1/2/3/4) for shell/CI composition
- [x] Setup docs in `docs/getting-started/judge-setup.md`
- [x] No MCP server, no classifier, no PostToolUse hook in V0

**V1 (after V0 validates the concept):**
- [ ] Graduate to `--judge[=model]` flag once Flag System ships
- [ ] Multi-model ensemble (`--judge=ensemble` queries GPT + Gemini, requires consensus)
- [ ] Opt-in PostToolUse hook for specific file patterns (e.g., `migrations/**/*.sql`)

**V2 (when usage data justifies it):**
- [ ] MCP server wrapper (reduces latency via connection reuse)
- [ ] High-stakes classifier using `routing.json` agent tier signal
- [ ] Cost dashboard + per-project budget controls

**Why V0 first:** validates the core hypothesis ("does a second model actually catch things Claude misses on DE tasks?") in ~150 lines of bash/python. If V0 doesn't deliver value after 10 real uses, we've lost a day. If it does, V1 is an incremental upgrade, not a rewrite.

**References:** llm-council-action GitHub Action, SEAR research paper, Openlayer LLM-as-Judge guide

---

### 🔵 P1: KB Freshness System

**Description:** Automatically detect stale KB content and validate against live documentation via MCP servers.

**Tasks:**
- [ ] Add `freshness_policy` metadata to `_index.yaml` for each domain
- [ ] Create `/kb-refresh` command that audits KB age
- [ ] Integrate `context7` MCP for live doc validation
- [ ] Integrate `exa` MCP for pattern verification
- [ ] Generate diff reports: outdated vs current content
- [ ] Add freshness badges to agent prompts (Fresh/Stale indicators)
- [ ] Schedule monthly background validation run
- [ ] Document refresh workflow

---

### 🔵 P1: Memory Echo System

**Description:** Persistent graph memory — agents remember what worked, what failed, and team conventions across sessions.

**Tasks:**
- [ ] Design echo directory structure (`.echo/knowledge.db`, `daily/`, `topics/`, `ECHO.md`)
- [ ] Build or integrate graph memory MCP server (evaluate MemoryGraph, MegaMemory, MemLayer)
- [ ] Implement 4-tier memory consolidation (raw → facts → concepts → narratives)
- [ ] Add PostToolUse hook to capture observations
- [ ] Implement LLM-based fact extraction with typed categories (decision, preference, pattern, error, convention)
- [ ] Build semantic search over stored memories
- [ ] Add ECHO.md index injection at SessionStart
- [ ] Implement decay policies (90-day TTL for unused memories)
- [ ] Document privacy controls (per-project isolation)

**References:** Mem0 (41K stars), agentmemory, MemoryGraph, agent-context project

---

## v4.0 — High Complexity (Strategic Features)

### ⚪ P1: Agents Composition (Serial & Parallel)

**Description:** Formalized composition patterns — chain agents serially (A→B→C) or fan out parallel (A||B||C) with merge strategies.

**Tasks:**
- [ ] Define composition DSL in YAML (serial, parallel, background)
- [ ] Create `/compose` command for ad-hoc compositions
- [ ] Build composition engine in workflow contracts
- [ ] Implement merge strategies (synthesis, diff, consensus)
- [ ] Add file reservation system for parallel writes (prevent conflicts)
- [ ] Define standard compositions (full-pipeline-build, codebase-audit, migration)
- [ ] Update `/pipeline`, `/build`, `/schema` commands to use compositions
- [ ] Document composition patterns in docs

**References:** Swarm-Tools, maestro-orchestrate, Sema Code

---

### ⚪ P1: Agentic Architect (Meta-Agent)

**Description:** A T3 agent that uses AgentSpec to evolve AgentSpec — creates new agents, KB domains, commands, and compositions.

**Tasks:**
- [ ] Create `agentspec-architect` agent (Opus, T3)
- [ ] Implement "design new agent" capability (reads `_template.md`, generates compliant files)
- [ ] Implement "create KB domain" capability (reads templates, generates full domain)
- [ ] Implement "compose command" capability (chains KB → agent → command)
- [ ] Implement "evolve agent" capability (reads usage patterns, proposes improvements)
- [ ] Integrate with `build-plugin.sh` (auto-validate + rebuild)
- [ ] Add safety gates (human approval for new agents)

---

### ⚪ P2: Overnight SubAgent

**Description:** Autonomous overnight execution — agent runs large tasks while developer sleeps, delivers PRs by morning.

**Tasks:**
- [ ] Create `overnight-builder` agent (Opus, T3)
- [ ] Implement planner→executor topology
- [ ] Build checkpointing system (git worktree, decision boundary snapshots)
- [ ] Add auto-approval whitelist (safe ops) + escalation list (destructive ops)
- [ ] Implement token/cost budget controls
- [ ] Integrate with `/schedule` skill for cron triggers
- [ ] Build morning status report PR generator
- [ ] Add circuit breakers and retry logic
- [ ] Document overnight workflow with examples

**References:** Level 3 autonomy patterns, Temporal workflow engine, Claude Code Remote Control

---

### ⚪ P2: Agent Teams Integration

**Description:** Peer-to-peer agent collaboration using Claude Code's experimental Agent Teams feature.

**Tasks:**
- [ ] Define team YAML schema (lead, modeler, builder, quality, reviewer roles)
- [ ] Create `/team` command for team dispatch
- [ ] Build team compositions for common DE workflows (pipeline-team, migration-team, audit-team)
- [ ] Implement cross-agent messaging patterns
- [ ] Add shared team memory (reads/writes to same Echo store)
- [ ] Document token cost warnings (15x single-session usage)
- [ ] Add team observability (per-agent activity, message logs)

**References:** Claude Code `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`

---

## v4.1 — Strategic Expansion

### ⚫ P2: Codex & Claude Cross-Platform

**Description:** Extend AgentSpec beyond Claude Code — make it work with Codex, OpenClaw, Cursor via MCP-first distribution.

**Tasks:**
- [ ] Add `build_codex_plugin()` to build-plugin.sh
- [ ] Add `build_mcp_only()` target for universal distribution
- [ ] Create MCP-only package (KB + routing as MCP tools)
- [ ] Write AGENTS.md conversion layer (agents → AGENTS.md sections)
- [ ] Test with Codex, OpenClaw, Cursor
- [ ] Document cross-platform installation

---

### ⚫ P3: Decision Ledger

**Description:** Structured log of every agent decision — compounding institutional memory.

**Tasks:**
- [ ] Design Decision Ledger schema (decision, alternatives, reasoning, outcome)
- [ ] Add PostToolUse hook to capture decisions
- [ ] Store in Echo memory graph
- [ ] Build `/decisions` query command
- [ ] Add visual timeline via visual-explainer

---

### ⚫ P2: Schema Evolution Agent

**Description:** Detect source schema drift and auto-propose downstream model updates.

**Tasks:**
- [ ] Create `schema-evolution-agent` (Opus, T3)
- [ ] Integrate with schema registries (Snowflake, BigQuery, Databricks)
- [ ] Build drift detection via MCP
- [ ] Auto-generate dbt model updates
- [ ] Add contract violation alerts

---

### ⚫ P3: Cost Optimization Agent

**Description:** Analyze warehouse spend and recommend partitioning, materialized views, caching.

**Tasks:**
- [ ] Extend `data-platform-engineer` with live cost data
- [ ] Integrate Snowflake/Databricks/BigQuery cost APIs via MCP
- [ ] Generate cost reduction reports
- [ ] Add `/cost-audit` command

---

## Ongoing Improvements

### 🔵 P2: Plugin Marketplace Distribution

**Tasks:**
- [ ] Submit to Dan Ávila's marketplace
- [ ] Submit to ComposioHQ/awesome-claude-plugins
- [ ] Create landing page / demo video
- [ ] Write launch blog post

---

### ⚪ P2: Telemetry

**Description:** Local usage tracking (opt-in) — which agents used, which KB domains loaded, which commands invoked.

**Tasks:**
- [ ] Design telemetry schema (privacy-first, local-only)
- [ ] Add opt-in flag in CLAUDE.md
- [ ] Implement collection hook
- [ ] Build `/telemetry` command for local reports

---

### ⚪ P3: `CLAUDE.md.template`

**Description:** Template file for user projects that includes routing rules, team conventions, and AgentSpec integration.

**Tasks:**
- [ ] Create `CLAUDE.md.template` with standard sections
- [ ] Add placeholders for project-specific config
- [ ] Document customization in getting-started guide

---

### ⚪ P3: KB CI Linting

**Description:** Automated lint step that catches dead KB references before they ship.

**Tasks:**
- [ ] Build lint script (extract `.claude/kb/` paths from agents, verify all exist)
- [ ] Integrate into `build-plugin.sh`
- [ ] Add GitHub Actions workflow
- [ ] Add frontmatter schema validation

---

### ⚪ P3: Semantic KB References Cleanup

**Description:** Review agents whose KB refs work but are semantically loose (e.g., supabase-specialist old RLS → rag-pipelines fallback).

**Tasks:**
- [ ] Audit all agent→KB reference mappings for semantic fit
- [ ] Create missing KB domains where needed (qdrant/, langfuse/)
- [ ] Update agents to use semantically correct references

---

## Nice-to-Haves

- Visual HTML dashboard for `/status` output
- `/agent-profile` command (show individual agent capabilities and usage)
- Export KB domain as standalone package (for sharing specific domains)
- AgentSpec playground — interactive web demo
- Video walkthroughs for each command
- Slack/Discord community

---

## Completed Reference (v3.0.0 and earlier)

See CHANGELOG.md for full version history.

---

**To add items:** Edit this file directly or open an issue. Keep the priority/status legend consistent.
