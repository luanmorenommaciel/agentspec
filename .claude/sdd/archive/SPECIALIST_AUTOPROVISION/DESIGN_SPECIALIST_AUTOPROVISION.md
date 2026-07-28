# DESIGN: Specialist Autoprovision

> Technical design for implementing SPECIALIST_AUTOPROVISION — design-time specialist-gap detection with a JIT provisioning sub-flow and a build-time safety net.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SPECIALIST_AUTOPROVISION |
| **Date** | 2026-07-28 |
| **Author** | design-agent (interactive session; match semantics user-confirmed) |
| **DEFINE** | [DEFINE_SPECIALIST_AUTOPROVISION.md](./DEFINE_SPECIALIST_AUTOPROVISION.md) |
| **Status** | ✅ Shipped |

---

## Architecture Overview

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                    SPECIALIST AUTOPROVISION — SYSTEM DIAGRAM                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  sdd-design Step 4 (agent matching)                                        │
│  ┌──────────────────────────────┐                                          │
│  │ For each manifest file:      │    citation found                        │
│  │ resolve domain → citation ───┼──────────────────────► manifest entry    │
│  │ against ORACLE               │                        (@agent + signal) │
│  └──────────────┬───────────────┘                                          │
│                 │ no citation possible = GAP                               │
│                 ▼                                                          │
│  ┌─────────────────────────────────────────────────────┐                   │
│  │      specialist-autoprovision SKILL (sub-flow)      │                   │
│  │                                                     │                   │
│  │  1. component-model gate ──► layer? (skill|agent)   │                   │
│  │  2. author via create-skill / create-agent SOP      │                   │
│  │  3. regenerate router (generate-agent-router.py)    │                   │
│  │  4. verify: new entry citable in routing.json ──────┼─► manifest entry  │
│  │     (core checklist items binding; doc items        │                   │
│  │      appended to manifest as build tasks)           │                   │
│  └─────────────────────────────────────────────────────┘                   │
│                 ▲                                                          │
│                 │ @agent unresolvable at delegation (drift)                │
│  ┌──────────────┴───────────────┐                                          │
│  │ sdd-build Delegation         │      ORACLE                              │
│  │ (safety net — same sub-flow) │      .claude/skills/agent-router/        │
│  └──────────────────────────────┘      routing.json (regenerated from      │
│                                        agent frontmatter — never drifts)   │
│                                                                            │
│  sdd-autopilot: Gate P row — proceed / retry(1) / abort — never asks       │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| `specialist-autoprovision` skill (NEW) | Owns the methodology: citation-based gap sensor, provisioning sub-flow orchestration (layer gate → SOP authoring → router regeneration → core-checklist validation), supervised/autonomous conduct fork, provenance row shape | Markdown skill, distributed (mirrored into `plugin/`) |
| `sdd-design` hook (MODIFY) | Thin step appended to Step 4: after matching, every manifest row must carry a citation or enter the sub-flow; the manifest finalizes only when 100% of rows resolve | Markdown edit — one hook, no methodology |
| `sdd-build` hook (MODIFY) | Thin safety-net branch in the Delegation decision flow: `@agent` unresolvable at delegation time → invoke the same sub-flow before delegating | Markdown edit — one hook, no methodology |
| `sdd-autopilot` Gate P (MODIFY) | One gate row (sensor, PASS, recoverable, budget, terminal, unavailable) + one conduct-override line for the layer fork | Markdown edit — policy only |
| Availability oracle (REUSED) | `.claude/skills/agent-router/routing.json` + generated `SKILL.md` — regenerated from agent frontmatter by `scripts/generate-agent-router.py` | Existing; unchanged |
| Authoring SOPs (REUSED) | `component-model` (layer gate), `create-agent` / `create-skill` (contracts + ship checklists) | Existing; unchanged |

New logic lands exactly once, in the skill (CAPABILITY layer per `.claude/kb/shared/component-model.md`); the three phase skills gain hooks, never methodology.

---

## Key Decisions

### Decision 1: Match semantics — mandatory citation, no numeric threshold

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted (user-confirmed 2026-07-28) |
| **Date** | 2026-07-28 |

**Context:** The DEFINE delegated the core sensor question to this phase: what precisely counts as "the inventory covers this domain"? The sensor decides component creation, so it must be auditable and must not oscillate between runs.

**Choice:** A task domain **resolves** if and only if the designer can record a **citation** — a specific inventory entry plus the covering signal:

- an agent in `routing.json`, cited as `{agent-name, signal}` where the signal is a `kb_domains` hit or explicit description coverage; **or**
- an existing skill (`.claude/skills/<name>/SKILL.md`) whose description covers the capability — execution then stays `(general)` with that skill loaded, and this is **not** a gap.

No citable entry → gap → provisioning sub-flow. The citation is recorded in the manifest's Agent column and the Agent Assignment Rationale table.

**Rationale:** Binary and auditable — a post-run reviewer can check every citation against `routing.json` mechanically. It uses both signals the router actually publishes (`kb_domains` and the description one-liner extracted from frontmatter), and it produces no pseudo-precise numbers. The skill-citation clause keeps the sensor honest about capabilities that are deliberately skills, preventing agent sprawl for capability-shaped gaps.

**Alternatives Rejected:**
1. Numeric confidence threshold (gap if score < 0.80) — LLM-assigned scores are not reproducible run-to-run; a non-deterministic sensor deciding component creation means the same DESIGN could provision on Tuesday and not on Wednesday.
2. Strict `kb_domains`-only matching — deterministic but blind to description coverage; agents like `shell-script-specialist` (no KB domain, description-covered) would trigger false gaps and duplicate specialists, pressuring the anti-sprawl gate the feature must respect.

**Consequences:**
- Trade-off accepted: citation judgment is still LLM-exercised — mitigated by requiring the citation to be recorded (checkable) rather than trusting an unrecorded match.
- Benefit gained: zero new matching infrastructure; the sensor is the artifact the repo already regenerates from frontmatter.

---

### Decision 2: Ship-checklist scheduling — core synchronous, docs deferred to the manifest

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-28 |

**Context:** The DEFINE mandates quality parity (same ship checklist as hand-authored components), but the `create-agent`/`create-skill` checklists include repo-release steps (plugin rebuild, catalogs, counts, CHANGELOG) that would bloat a mid-design provisioning pause.

**Choice:** Split by what delegation actually requires. **Core items run synchronously inside the sub-flow** and are binding before any delegation: scaffold from template, complete frontmatter contract, router regeneration, and citation verification of the new entry. **Deferred items are appended to the file manifest as ordinary build tasks**: plugin mirror rebuild, catalog/README updates, count references, CHANGELOG entry.

**Rationale:** The delegation precondition is "the router resolves the specialist" — nothing else blocks execution. The deferred items remain binding because they become manifest tasks the Build must complete and the existing Gate B (100% task completion) and Gate S (pre-ship checklist) already verify. The checklist is scheduled, never relaxed.

**Alternatives Rejected:**
1. Run all 7 checklist items synchronously — blocks the design phase on doc bookkeeping that no delegation depends on.
2. A reduced "generated tier" checklist — explicitly forbidden by the DEFINE (no relaxed generated tier).

**Consequences:**
- Trade-off accepted: between provisioning and build completion, the repo transiently holds a specialist not yet in the catalogs (bounded by the run itself).
- Benefit gained: design-phase latency on a gap stays proportional to authoring the component, not to repo bookkeeping.

---

### Decision 3: Gate P policy — retry 1, abort on exhaustion, visible-skip degradation

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-28 |

**Context:** Autonomous runs need a proceed/retry/abort rule for provisioning; the sensor may itself be unavailable (router script missing in a broken checkout); the DEFINE fixes abort-on-budget-exhaustion (AT-006) and forbids ask branches.

**Choice:** Add **Gate P** to the `sdd-autopilot` gate policy table:

- **Sensor:** post-regeneration citation check — the new component's entry is citable in `routing.json` (agents) or on disk with valid frontmatter (skills), core checklist items passing.
- **PASS:** citation verified → proceed with delegation.
- **Recoverable:** authoring or validation failure → regenerate the component once with the violations in context (mirrors Gate L's regeneration semantics). **Budget: 1 per gap.**
- **Terminal:** budget exhausted → ABORT with a gap report naming the domain, attempts, and failing checks (per DEFINE AT-006).
- **Sensor unavailable:** `generate-agent-router.py` not executable / oracle unreadable → **VISIBLE SKIP** row + fall back to `(general)` execution with a WARN ledger row — the pre-feature status quo, degraded loudly, never assumed as PASS.

No change to `WORKFLOW_CONTRACTS.yaml`: autopilot adds policy, not sensors, and this sensor's contract is already owned by `create-agent` (frontmatter/parser contract) and `scripts/generate-agent-router.py`.

**Rationale:** Consistent with every existing gate: finite budget, terminal abort with actionable report, visible-skip on sensor unavailability (the `sdd-autopilot` anti-pattern table forbids treating sensor absence as PASS). Fallback-to-`(general)` on sensor unavailability is safe because it is exactly today's behavior — the feature can degrade to the status quo but never below it.

**Alternatives Rejected:**
1. Abort on sensor unavailability — makes a broken linter-class dependency fatal when a safe status-quo fallback exists; inconsistent with Gate L/J skip semantics.
2. Silent `(general)` fallback on budget exhaustion — contradicts DEFINE AT-006 and hides exactly the degradation this feature exists to eliminate.

**Consequences:**
- Trade-off accepted: a hard abort on a persistent authoring failure even though `(general)` could limp through — visibility over completion, per the DEFINE's problem statement.
- Benefit gained: the non-blocking invariant holds with zero new gate machinery concepts.

---

### Decision 4: Supervised fork conduct — one question, only at the layer gate

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-28 |

**Context:** The DEFINE (SHOULD) allows supervised sessions to ask at the layer-decision fork; autonomous runs must not.

**Choice:** The skill defines exactly one permissible question in supervised mode — the `component-model` layer fork (skill vs. agent vs. extend-existing) when the gate's four conditions do not decide it cleanly. Autonomous mode maps the same fork to: assume **skill + thin executor** (the conservative default — `component-model` documents that most "new agent" requests are skills), record `[ASSUMED]`, proceed.

**Rationale:** The layer decision is the only genuinely user-owned fork in the sub-flow (everything downstream is contract-mechanical), and the conservative default minimizes irreversibility — a skill can later gain a thin executor; an unnecessary agent pressures the anti-sprawl gate.

**Alternatives Rejected:**
1. Ask at every sub-flow step in supervised mode — turns provisioning into a wizard; contradicts the intention-driven goal.
2. Never ask even in supervised mode — discards cheap human signal that is available by definition in that mode.

**Consequences:**
- Trade-off accepted: autonomous runs may occasionally create a skill where a human would have chosen an agent — recorded, reviewable, reversible.
- Benefit gained: identical sub-flow in both modes; only the fork resolution differs.

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `.claude/skills/specialist-autoprovision/SKILL.md` | Create | The methodology: citation sensor, sub-flow steps, conduct fork, provenance shape, hygiene gate | (general) | None |
| 2 | `.claude/skills/sdd-design/SKILL.md` | Modify | Append gap-resolution hook to Step 4 + quality-gate line ("every manifest row carries a citation") | (general) | 1 |
| 3 | `.claude/skills/sdd-build/SKILL.md` | Modify | Safety-net branch in the Delegation decision flow (unresolvable `@agent` → sub-flow) | (general) | 1 |
| 4 | `.claude/skills/sdd-autopilot/SKILL.md` | Modify | Gate P row in the gate policy table + one conduct-override line (layer fork) | (general) | 1 |
| 5 | `CHANGELOG.md` | Modify | `[Unreleased]` entry for the feature | (general) | 1–4 |
| 6 | `CLAUDE.md` | Modify | Skill counts, skills-directory comment, Key Files row for the new skill | (general) | 1 |
| 7 | `docs/reference/README.md` | Modify | Skill catalog entry | (general) | 1 |
| 8 | `README.md` + `docs/README.md` + `plugin/README.md` | Modify | Skill-count references (per create-skill ship checklist item 3) | (general) | 1 |
| 9 | `plugin/` tree | Regenerate | `./build-plugin.sh` — mirrors the new distributed skill and rewritten paths; never hand-edited | (general) | 1–8 |

**Total Files:** 9 manifest rows (8 authored + 1 regenerated tree)

---

## Agent Assignment Rationale

> Agents discovered from `.claude/agents/` — Build phase invokes matched specialists.

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| (general) | 1–9 | Applying Decision 1's own citation rule to this manifest: no `routing.json` agent covers skill/framework authoring, but the capability **is** covered by citable skills — `create-skill`, `component-model`, and the upstream `skill-creator` — so per the skill-citation clause this is `(general)` execution with those skills loaded, **not** a gap. This manifest is the first worked example of the sensor it designs. |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md` (58 agents via `routing.json`, version 1)
- Matched by: Decision 1 citation rule — `kb_domains` signal, description signal, or covering-skill citation

---

## Code Patterns

### Pattern 1: Gap-resolution hook (inserted into `sdd-design` Step 4)

```markdown
#### Step 4.5: Resolve every assignment against the inventory (specialist-autoprovision)

Before finalizing the manifest, load `.claude/skills/specialist-autoprovision/SKILL.md`
and apply its citation rule to every row:

- Row cites a routing.json agent entry (name + kb_domains/description signal) → resolved.
- Row cites a covering skill → resolved as `(general)` with that skill loaded.
- No citation possible → GAP: run the skill's provisioning sub-flow; the manifest
  finalizes only after the new component's citation verifies.

Record every citation in the Agent Assignment Rationale table; record every
provisioning event per the skill's provenance shape.
```

### Pattern 2: Gate P row (inserted into the `sdd-autopilot` gate policy table)

```markdown
| **P — Provision** | specialist-autoprovision citation check after `scripts/generate-agent-router.py` regeneration | new component citable in the oracle, core checklist items pass → proceed | authoring/validation failure → regenerate the component once with violations in context | 1 per gap | budget exhausted → ABORT, gap report names domain, attempts, failing checks | script not executable / oracle unreadable → VISIBLE SKIP row, fall back to `(general)` + WARN — never assume PASS |
```

### Pattern 3: Router regeneration + citation verification (the sub-flow's binding step)

```bash
python3 scripts/generate-agent-router.py

# Agents: the regenerated oracle must resolve the new specialist by name
grep -q "\"name\": \"${NEW_AGENT_NAME}\"" .claude/skills/agent-router/routing.json

# Skills: on-disk presence with parseable frontmatter is the citation
test -f ".claude/skills/${NEW_SKILL_NAME}/SKILL.md"
```

### Pattern 4: Provenance row shape (RUN REPORT / BUILD_REPORT)

```markdown
| Component | Layer | Trigger Domain | Phase | Fork Resolution | Validation |
|-----------|-------|----------------|-------|-----------------|------------|
| terraform-modules (skill) | skill + thin executor | terraform | design (Gate P) | [ASSUMED] conservative default | core checklist PASS; docs items → manifest rows 10–12 |
```

---

## Data Flow

```text
1. sdd-design Step 4 assigns agents to manifest files (existing behavior)
   │
   ▼
2. Step 4.5 hook: each row resolves via citation against routing.json / skills
   │
   ├─ citation found ────────────────────────────► row finalized
   │
   ▼ (no citation = gap)
3. specialist-autoprovision sub-flow:
   component-model layer gate → create-skill/create-agent SOP authoring
   → regenerate router → verify citation (Pattern 3)
   │
   ├─ supervised: layer fork MAY ask (Decision 4) — everything else mechanical
   ├─ autonomous: Gate P (proceed / retry 1 / abort) — never asks
   │
   ▼
4. Citation verifies → manifest row finalized with @new-specialist;
   deferred checklist items appended as manifest build tasks (Decision 2);
   provenance row written (Pattern 4)
   │
   ▼
5. sdd-build delegates per manifest; safety net: an unresolvable @agent at
   delegation time re-enters step 3 before any delegation (drift case)
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-----------------|----------------|
| `scripts/generate-agent-router.py` | Local CLI (Bash) — oracle regeneration | None (local) |
| `routing.json` / agent frontmatter | File read — availability oracle | None (local) |
| Task tool (subagent delegation) | Claude Code runtime — unchanged delegation path | Session |
| `tools/spec-linter/spec-lint` | Unchanged — phase documents only; no new linter binding | None (local) |

No network, no cloud services, no new external dependencies.

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Structural | Router regeneration determinism; plugin mirror integrity | `routing.json`, `plugin/` | `python3 scripts/generate-agent-router.py --check`; `./build-plugin.sh` + `git diff --exit-code plugin/` | Zero drift (CI-enforced) |
| Contract | Modified skills remain valid (frontmatter parses, referenced files exist) | Manifest rows 1–4 | `./build-plugin.sh` (fails on broken skill frontmatter) | 100% of modified skills |
| Scenario | AT-001/002/003: citation resolution, gap detection, layer-gate routing | Fixture design session with a deliberately uncovered domain (e.g., `elixir` — no agent or skill cites it) | Supervised `/design` dry run on a scratch branch | AT-001–003 exercised |
| Scenario | AT-004: build-time safety net | Manifest hand-edited to reference a non-existent `@agent` | Supervised `/build` dry run | AT-004 exercised |
| Scenario | AT-005/006/007: non-blocking conduct, retry-budget abort, provenance rows | Autopilot smoke run with an uncovered domain in the intent | `/auto` on a scratch branch; inspect RUN REPORT ledger | AT-005–007 exercised |
| Hygiene | AT-scope: no private context in generated components | Generated component files | Case-insensitive grep against the maintainer's private-context sanitization list (kept outside the repo, never committed) → zero hits | 100% of generated files |

Every DEFINE acceptance test (AT-001 … AT-007) maps to a scenario row above.

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| Generated component fails core checklist (frontmatter incomplete, citation unverifiable) | Regenerate once with the violations in context; then Gate P terminal (auto: ABORT + gap report; supervised: surface to user) | Yes (1) |
| `generate-agent-router.py` not executable / crashes | VISIBLE SKIP + `(general)` fallback + WARN ledger row (status-quo degradation, never silent) | No |
| Oracle (`routing.json`) missing or unparseable | Regenerate first; if still unreadable, same degradation as above | Yes (1, via regeneration) |
| Layer fork ambiguous (four-condition gate does not decide) | Supervised: single AskUserQuestion (Decision 4). Autonomous: assume skill + thin executor, record `[ASSUMED]` | No — fork, not failure |
| Private-context leak detected in a generated component (hygiene grep hits) | Block the component; regenerate without run-specific private data — counts against the same per-gap budget | Yes (within budget) |
| Gap detected for a domain already provisioned earlier in the same run | Cite the just-created component — the regenerated oracle resolves it; never provision twice for one domain | n/a |

---

## Configuration

No new config files — the feature is skill policy, not tunable runtime code. Policy constants and their single-source owners:

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| Gate P retry budget | policy constant | `1` per gap | Owned by the Gate P row in `sdd-autopilot` — the only place it is stated |
| Autonomous layer-fork default | policy constant | skill + thin executor | Owned by `specialist-autoprovision` SKILL.md (Decision 4) |
| Oracle path | policy constant | `.claude/skills/agent-router/routing.json` | Owned by `specialist-autoprovision` SKILL.md; already the router generator's output contract |

---

## Security Considerations

- Public-repo hygiene is a blocking gate: generated components are grepped against the private-context list before they land; a hit blocks and regenerates (Error Handling) — never committed then cleaned.
- Generated agents get least-privilege tool lists per the `_template.md` tier guidance; the sub-flow never grants `Bash`/network tools by default to a specialist that only reads and writes files.
- Provenance rows record sensor presence/absence and decisions — never environment values, keys, or run-private data (inherits the `sdd-autopilot` RUN REPORT rule).
- No new executable surface: the sub-flow invokes only pre-existing repo scripts (`generate-agent-router.py`, `build-plugin.sh`).

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | Gate P ledger rows in the RUN REPORT (one per evaluation, including retries and visible skips) — appended when the gate resolves, never batched |
| Metrics | Provenance rows (Pattern 4) in RUN REPORT / BUILD_REPORT: every provisioning event with component, layer, trigger domain, fork resolution, validation outcome |
| Tracing | Citations in the DESIGN's Agent Assignment Rationale table — post-run audit path from every manifest row to the oracle entry that justified it; WARN rows for every degradation to `(general)` |

---

## Pipeline Architecture (if applicable)

N/A — framework tooling feature (AgentSpec developing AgentSpec); no data pipelines, partitions, or quality gates involved.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-28 | design-agent | Initial version — Decisions 1–4; match semantics (Decision 1) user-confirmed in session |
| 1.1 | 2026-07-28 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/ship .claude/sdd/features/DEFINE_SPECIALIST_AUTOPROVISION.md`
