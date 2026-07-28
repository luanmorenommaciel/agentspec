# BRAINSTORM: Specialist Autoprovision

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SPECIALIST_AUTOPROVISION |
| **Date** | 2026-07-28 |
| **Author** | brainstorm-agent (autonomous mode — self-answered per the sdd-autopilot Brainstorm conduct override); key assumptions ratified interactively by the user on 2026-07-28 |
| **Status** | ✅ Shipped |

---

## Initial Idea

**Raw Input:** Notion brainstorm item *"2026-07-27 · Brainstorm AgentSpec — intention-driven development e auto-criação de especialistas"* (captured via Telegram audio):

> AgentSpec is being expanded into intention-driven development: the user states intent/problem/context and the autonomous workflow executes end to end; humans enter the loop only on ambiguity or deviation from the expected. When the workflow reaches implementation (e.g., Terraform infrastructure), there must be an automatic flow that checks whether a specialist subagent exists for that domain and, when it doesn't, creates the specialist following the documentation best practices that already exist in AgentSpec itself — the same for Python, front-end, testing, GitHub, Google Cloud. If no skill or agent can solve the implementation problem, the specialist must be created **before** execution is delegated.

**Context Gathered:**

- Autopilot V0 (`/auto` + headless runner) shipped and was archived 2026-07-27 — the intention-driven loop already exists; gates decide, never a human (`.claude/skills/sdd-autopilot/SKILL.md`).
- The DESIGN phase already produces an **agent-matched file manifest** (`sdd-design`), and `sdd-build` delegates per that manifest (`@agent-name` → Task tool, `(general)` → direct execution) with a data-engineering delegation map.
- The specialist inventory is machine-readable today: `scripts/generate-agent-router.py` regenerates the `agent-router` skill (`SKILL.md` + `routing.json`) from agent frontmatter — 58 agents across 8 categories.
- The "documentation best practices" the Notion item refers to already exist as authoring SOPs: `component-model` (layer-decision gate), `create-agent` (frontmatter contract + ship checklist), `create-skill` (naming, placement, build checklist).
- `.claude/agents/README.md` carries the four-condition "When NOT to Create an Agent" gate (no existing agent covers >60%, unique KB/tool combination, ≥3 distinct triggers, no >80% overlap) — the anti-sprawl control a creation flow must respect.

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | New skill `.claude/skills/specialist-autoprovision/` + thin hook steps in `sdd-design` and `sdd-build` + one gate row in `sdd-autopilot` | The methodology is a CAPABILITY → skill layer per the component model; phases gain hooks, not logic |
| Relevant KB Domains | `genai` (multi-agent-systems, agentic-workflow, guardrails), `prompt-engineering` (system-prompts), `shared/component-model.md` | Patterns to consult during Define/Design |
| IaC Patterns | N/A — framework tooling feature | No infrastructure required |

---

## Discovery Questions & Answers

> Autonomous run: every answer is self-derived from KB + codebase evidence and flagged `[ASSUMED]` where the Notion item did not state it explicitly.

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Where in the workflow should the availability check live? | At the Design→Build boundary: when `sdd-design` matches agents to the file manifest, every unresolvable domain is a gap; `sdd-build` keeps a safety net for delegation that hits a missing agent at run time. `[ASSUMED — derived from codebase: the manifest is where agent assignment already happens; ratified by user 2026-07-28]` | Hooks the check where the decision already exists; no new orchestration layer |
| 2 | Who uses this? | Primary: autonomous `/auto` runs (no human in the loop). Secondary: supervised `/design` + `/build` sessions. *(Grounded in the Notion item)* | The flow must satisfy the autopilot non-blocking invariant — proceed/retry/abort, never ask |
| 3 | What counts as "a specialist exists"? | A routing match in the generated router inventory (`routing.json` / agent frontmatter): an agent whose KB domains and description cover the task's domain, or an existing skill covering the capability. `[ASSUMED; ratified by user 2026-07-28]` | Gap sensor = the generated router artifact, not ad-hoc greps; it stays correct because it is regenerated from frontmatter |
| 4 | How is a new specialist created? | Through the existing SOPs, never a bespoke path: `component-model` gate decides the layer (most gaps are a skill + thin executor), then the `create-agent` / `create-skill` contracts, then `scripts/generate-agent-router.py` regeneration, then the same ship checklist as hand-authored components. *(Grounded: `create-agent` names this exact pipeline)* | "Best practices already in AgentSpec" is a hard requirement — reuse, don't restate |
| 5 | When does a human enter the loop? | Only on ambiguity or deviation: supervised mode may ask at the layer-decision fork; autopilot maps the fork to record-`[ASSUMED]`-and-proceed or abort per gate budgets. *(Grounded in the Notion item + the sdd-autopilot conduct table)* | Gate semantics must be written as policy in `sdd-autopilot`, not improvised at run time |

**Minimum Questions:** 3 ✅ (5 asked)

---

## Sample Data Inventory

> Samples improve LLM accuracy through in-context learning and few-shot prompting.

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | `.claude/agents/**/*.md` | 58 | Ground truth of well-formed agent frontmatter — few-shot corpus for generation |
| Output examples | `.claude/agents/_template.md` + the `duckdb-specialist` worked example in `create-skill`/`create-agent` | 2 | Target shape for a generated agent |
| Ground truth | `.claude/skills/agent-router/routing.json` (27.8K) + generated `SKILL.md` | 1 | Machine-readable inventory = the gap sensor |
| Related code | `scripts/generate-agent-router.py`, `.claude/skills/component-model/`, `.claude/skills/create-agent/`, `.claude/skills/create-skill/`, `sdd-build` delegation protocol | 5 | The pipeline to reuse verbatim |

**How samples will be used:**

- Few-shot examples when authoring a new specialist's frontmatter and body
- `routing.json` as the availability oracle (query before delegating)
- The `create-agent`/`create-skill` ship checklists as binding validation gates on generated components

---

## Approaches Explored

### Approach A: Design-time gap gate + JIT provisioning sub-flow ⭐ Recommended

**Description:** Add a specialist-availability step to `sdd-design`'s agent-matching: while building the file manifest, resolve each task domain against the router inventory. On a gap, enter a provisioning sub-flow — `component-model` gate (agent vs. skill vs. extend-existing) → author via `create-agent`/`create-skill` SOPs → regenerate the router → validate against the ship checklist — and only then finish the manifest. `sdd-build` keeps a safety-net instance of the same sub-flow for delegation that hits a missing agent. `sdd-autopilot` gains one gate row (proceed / retry-within-budget / abort-with-report) so autonomous runs never block.

**Pros:**
- Gap surfaces at the earliest point where needed domains are actually known (the file manifest) — before any delegation fails
- Reuses the documented authoring SOPs verbatim; zero new authoring logic
- Gate policy stays single-source in `sdd-autopilot`; methodology single-source in the new skill
- Build-time safety net catches drift between design and execution

**Cons:**
- Mid-run authoring lengthens the design phase when gaps exist
- A specialist created under run pressure risks lower quality — mitigated by making the ship checklists binding and router regeneration mandatory

**Why Recommended:** Confidence **0.85** — KB pattern (`shared/component-model.md` layering; `genai/agentic-workflow`) plus codebase match (manifest matching, router generator, and authoring SOPs all exist and compose). Not 0.95 because the auto-provision *loop itself* has no precedent in the repo.

---

### Approach B: Build-time just-in-time creation only

**Description:** Detect gaps solely inside `sdd-build`, at delegation time — when the manifest names an `@agent` that doesn't exist, or routes a specialized domain to `(general)`.

**Pros:**
- Single hook point; smallest diff
- Lazy — only creates specialists that are actually delegated to

**Cons:**
- The gap surfaces late, on the build's critical path, where failure is most expensive
- DESIGN can ship a manifest referencing agents that don't exist without anyone noticing
- Violates the design-decides / build-executes separation the workflow is built on

---

### Approach C: INTAKE-time capability sweep

**Description:** At autopilot INTAKE, scan the stated intent for likely domains and pre-create every missing specialist before Phase 0 begins.

**Pros:**
- No phase ever pauses for provisioning

**Cons:**
- The intent alone is a weak sensor — the file manifest doesn't exist yet, so domain inference is guesswork
- Over-provisions specialists that the run never delegates to (YAGNI violation)
- Duplicates knowledge that Design will derive properly two phases later

---

## Data Engineering Context (if applicable)

N/A — this is a framework tooling feature (AgentSpec developing AgentSpec); no data pipelines, sources, or SLAs involved.

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A |
| **User Confirmation** | ✅ Confirmed by user 2026-07-28 — interactive ratification session: Approach A, the routing.json oracle, and all 5 YAGNI removals explicitly ratified |
| **Reasoning** | Earliest reliable sensor (the agent-matched manifest) + full reuse of the existing authoring SOPs + build-time safety net; B is late and blind at design, C guesses without a manifest |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|----------------------|
| 1 | Gap sensor = the generated router inventory (`routing.json`) | Regenerated from agent frontmatter, so it cannot drift from reality | Ad-hoc grepping of agent files at run time |
| 2 | Layer decision delegated to the `component-model` gate | Most "new agent" gaps are actually a skill + thin executor; the four-condition gate in `agents/README.md` prevents agent sprawl | Always creating a full agent per gap |
| 3 | Generated components = hand-authored components: same contracts, same ship checklist; provenance recorded in the RUN REPORT / BUILD_REPORT | Quality parity and auditability | A separate "generated" tier with laxer rules |
| 4 | Gate semantics (proceed/retry/abort) added only to `sdd-autopilot` | Single-source policy invariant — entrypoints never restate rules | Encoding provisioning rules in the command or headless runner |
| 5 | New KB domains are NOT auto-created during provisioning | `kb-build` is a deliberate, high-assurance flow; a new specialist may ship with existing domains or `kb_domains: []` | Auto-running kb-build mid-run |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|-------------------|----------------|----------------|
| Auto-creating KB domains as part of provisioning | Expensive high-assurance flow; separate deliberate act | Yes |
| Pruning / GC of unused generated specialists | No evidence of sprawl yet; the four-condition gate already limits creation | Yes |
| Eval suite / quality scoring of generated specialists beyond the ship checklist | Judge V1+ territory (planned separately) | Yes |
| Propagating new specialists to vendored consumer repos in the same flow | `rollout-agentspec` already owns distribution | Yes |
| Pre-building KB coverage for front-end/GitHub/etc. domains | Specialists can ship with `kb_domains: []` when no domain exists | Yes |

> All 5 removals ratified by the user on 2026-07-28 — including the sensitive one: generated specialists may ship with `kb_domains: []` when no KB domain covers their territory.

---

## Incremental Validations

> Autonomous run: validations executed as self-checks against the repo's own contracts, per the conduct override.

| Section | Presented | Self-Validation | Adjusted? |
|---------|-----------|-----------------|-----------|
| Architecture concept vs. sdd-autopilot invariants | ✅ | Non-blocking invariant holds: gap → provision → finite retry budget → abort-with-report; no ask branch introduced | No |
| Component breakdown vs. component model | ✅ | New logic lands as a skill (CAPABILITY layer); `sdd-design`/`sdd-build` gain thin hook steps; no agent absorbs methodology | No |
| Sensor choice vs. router generator contract | ✅ | `routing.json` is regenerated from frontmatter; the parser pitfalls (inline `kb_domains`, `target:` lines) are documented in `create-agent` | Yes — router regeneration promoted to a mandatory post-authoring step in the flow |

**Minimum Validations:** 2 ✅ (3 completed)

---

## Suggested Requirements for /define

### Problem Statement (Draft)

An autonomous SDD run degrades or fails when the implementation phase needs a domain specialist (Terraform/infra, Python, front-end, testing, GitHub, GCP, …) that doesn't exist in the agent/skill inventory — today nothing detects that gap or fills it automatically before delegation.

### Target Users (Draft)

| User | Pain Point |
|------|------------|
| Matheus running `/auto` (intention-driven, lights-out) | Run silently degrades to `(general)` execution — or fails — when no specialist covers the domain |
| Supervised `/design` + `/build` users | Manual detour mid-feature to hand-author a missing agent |

### Success Criteria (Draft)

- [ ] During design (and as a build-time safety net), every task domain in the file manifest is automatically resolved against the specialist inventory
- [ ] A missing specialist triggers automatic creation following the `component-model` gate and the `create-agent`/`create-skill` SOPs, **before** delegation
- [ ] A generated specialist passes the same ship checklist and router regeneration as a hand-authored one
- [ ] Execution is delegated only after the router resolves the new specialist
- [ ] Humans enter the loop only on ambiguity: supervised mode may ask at the layer fork; autopilot resolves per gate policy (assume-and-record or abort) — never blocks
- [ ] Every provisioning event is recorded (RUN REPORT / BUILD_REPORT row with provenance)

### Constraints Identified

- The autopilot non-blocking invariant is inviolable — no ask branch anywhere in the flow
- Single-source policy: gate rules live only in `sdd-autopilot`; methodology only in the new skill; entrypoints restate nothing
- Reuse the existing authoring SOPs — no parallel authoring path
- Router regeneration (`scripts/generate-agent-router.py`) is mandatory after any creation; respect its parser contract (inline `kb_domains`, clean first description line)
- Public repo hygiene: generated components must not embed private context (client names, credentials)

### Out of Scope (Confirmed)

- Auto-creation of KB domains during provisioning
- Judge/eval scoring of generated specialists (Judge V1+)
- Rollout of generated specialists to vendored consumer repos (owned by `rollout-agentspec`)
- Lifecycle management (pruning, deprecation) of generated specialists

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 5 (self-answered, autonomous mode) |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 5 |
| Validations Completed | 3 (self-validations) + interactive user ratification of all `[ASSUMED]` decisions |
| Duration | Autonomous session + interactive ratification (both 2026-07-28) |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_SPECIALIST_AUTOPROVISION.md`
