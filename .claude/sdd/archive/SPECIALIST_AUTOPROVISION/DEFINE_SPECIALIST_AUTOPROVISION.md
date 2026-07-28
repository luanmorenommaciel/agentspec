# DEFINE: Specialist Autoprovision

> Automatic detection and just-in-time creation of missing specialist agents/skills before implementation is delegated — so intention-driven runs never degrade to generalist execution.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SPECIALIST_AUTOPROVISION |
| **Date** | 2026-07-28 |
| **Author** | define-agent (input: user-ratified BRAINSTORM_SPECIALIST_AUTOPROVISION.md) |
| **Status** | ✅ Shipped |
| **Clarity Score** | 14/15 |

---

## Problem Statement

An autonomous SDD run degrades or fails when the implementation phase needs a domain specialist (Terraform/infra, Python, front-end, testing, GitHub, GCP, …) that doesn't exist in the agent/skill inventory — today nothing detects that gap, so work silently falls to `(general)` execution or the delegation fails mid-build, and the only fix is a manual detour to hand-author the missing specialist.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Autopilot operator (Matheus) | Runs `/auto` intention-driven, lights-out | Run silently degrades to `(general)` execution — or fails — when no specialist covers a needed domain; discovers it only in the RUN REPORT |
| Supervised SDD user | Runs `/design` + `/build` interactively | Must interrupt the feature mid-flight to hand-author a missing agent/skill, then wire the router, before resuming |

---

## Goals

What success looks like (prioritized):

| Priority | Goal |
|----------|------|
| **MUST** | Design-time gap gate: while `sdd-design` builds the agent-matched file manifest, every task domain is resolved against the generated router inventory (`routing.json`); unresolvable domains are detected as gaps before the manifest is finalized |
| **MUST** | JIT provisioning sub-flow: a detected gap triggers `component-model` layer gate → `create-agent`/`create-skill` SOP authoring → mandatory router regeneration → ship-checklist validation, all **before** delegation |
| **MUST** | Quality parity: a generated specialist satisfies the same contracts and ship checklist as a hand-authored one — no relaxed "generated" tier |
| **MUST** | Autopilot gate policy: one gate row added to `sdd-autopilot` (proceed / retry-within-budget / abort-with-gap-report) so autonomous runs never block on provisioning |
| **SHOULD** | Build-time safety net: `sdd-build` runs the same sub-flow when delegation hits a manifest entry whose agent doesn't resolve at run time (design→build drift) |
| **SHOULD** | Provenance: every provisioning event is recorded as a RUN REPORT / BUILD_REPORT row (what was created, which layer, trigger, validation outcome) |
| **SHOULD** | Supervised-mode fork: in interactive sessions, the layer-decision fork may ask the user (AskUserQuestion); in autonomous mode it maps to record-`[ASSUMED]`-and-proceed or abort per gate policy |
| **COULD** | Gap summary in the DESIGN document even when provisioning succeeds (which domains were gaps, what was created) |

**Priority Guide:**
- **MUST** = MVP fails without this
- **SHOULD** = Important, but workaround exists
- **COULD** = Nice-to-have, cut first if needed

---

## Success Criteria

Measurable outcomes (must include numbers):

- [ ] 100% of task domains in the agent-matched file manifest are resolved against the specialist inventory during `sdd-design` (0 manifest entries referencing non-existent agents at design completion)
- [ ] 100% of detected gaps trigger the provisioning sub-flow (`component-model` gate → SOP authoring → router regeneration) before any delegation to that domain
- [ ] 100% of generated specialists pass the same ship checklist as hand-authored ones, and the router resolves them before execution is delegated (0 relaxed rules)
- [ ] 0 ask branches in autonomous mode: autopilot runs resolve every provisioning fork via gate policy (proceed / retry / abort) — never a human prompt
- [ ] 100% of provisioning events have a provenance row in the RUN REPORT / BUILD_REPORT
- [ ] Anti-sprawl holds: 0 generated agents that violate the four-condition gate in `.claude/agents/README.md` (>60% coverage overlap, missing unique KB/tool combination, <3 distinct triggers, >80% overlap with an existing agent)

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Existing specialist (happy path) | A manifest task domain covered by an existing agent in `routing.json` | `sdd-design` agent-matching runs | No provisioning occurs; the manifest references the existing agent |
| AT-002 | Gap detected at design | A task domain (e.g., Terraform infra) with no matching agent or skill in the router inventory | `sdd-design` agent-matching runs | The provisioning sub-flow executes (layer gate → SOP authoring → router regeneration) and the manifest finalizes only after the router resolves the new specialist |
| AT-003 | Layer gate routes to skill | A gap where the `component-model` gate concludes "skill + thin executor" | The provisioning sub-flow authors the component | A skill is created via the `create-skill` SOP — not a full agent — respecting the four-condition anti-sprawl gate |
| AT-004 | Build-time safety net | A manifest entry referencing an `@agent` that doesn't resolve at build time (drift) | `sdd-build` reaches that delegation | The same sub-flow provisions the specialist before delegating; the build does not fail on the missing agent |
| AT-005 | Autopilot never blocks | An autonomous run hits an ambiguous layer-decision fork during provisioning | Gate policy is applied | The run records `[ASSUMED]` and proceeds, or aborts with a gap report — no human prompt is issued |
| AT-006 | Retry budget exhausted | Generated component fails ship-checklist validation repeatedly | The `sdd-autopilot` retry budget for the provisioning gate is exhausted | The run aborts with a gap report naming the domain, the attempts, and the failing checks |
| AT-007 | Provenance recorded | A provisioning event completed during a run | The RUN REPORT / BUILD_REPORT is written | It contains a row with the component name, layer decision, trigger domain, and validation outcome |

---

## Out of Scope

Explicitly NOT included in this feature (all five YAGNI removals ratified by the user 2026-07-28):

- Auto-creation of KB domains during provisioning — `kb-build` is a deliberate, high-assurance flow; generated specialists may ship with `kb_domains: []`
- Pruning / GC / lifecycle management of generated specialists
- Eval or judge scoring of generated specialists beyond the ship checklist (Judge V1+ territory)
- Rollout of generated specialists to vendored consumer repos (owned by `rollout-agentspec`)
- Pre-building KB coverage for anticipated domains (front-end, GitHub, …)

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | Autopilot non-blocking invariant is inviolable — no ask branch anywhere in the autonomous flow | Gate semantics must be policy in `sdd-autopilot`, resolved at run time without a human |
| Technical | Single-source policy: gate rules live only in `sdd-autopilot`; methodology only in the new skill; entrypoints restate nothing | Design must place logic per the component model — phases gain thin hooks, not logic |
| Technical | Reuse the existing authoring SOPs (`component-model`, `create-agent`, `create-skill`) verbatim — no parallel authoring path | The sub-flow orchestrates existing skills; it never restates their contracts |
| Technical | Router regeneration (`scripts/generate-agent-router.py`) is mandatory after any creation; its parser contract binds (inline `kb_domains`, clean first description line) | A specialist "exists" only once the regenerated router resolves it |
| Process | The four-condition anti-sprawl gate in `.claude/agents/README.md` binds every creation decision | Most gaps should resolve to a skill + thin executor, not a new agent |
| Security | Public repo hygiene: generated components must not embed private context (client names, credentials) | Provisioning prompts must exclude run-specific private data from generated files |

---

## Technical Context

> Essential context for Design phase - prevents misplaced files and missed infrastructure needs.

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | New skill `.claude/skills/specialist-autoprovision/` + thin hook steps in `.claude/skills/sdd-design/SKILL.md` and `.claude/skills/sdd-build/SKILL.md` + one gate row in `.claude/skills/sdd-autopilot/SKILL.md` | Methodology is a CAPABILITY → skill layer per the component model; phases gain hooks, not logic |
| **KB Domains** | `genai` (multi-agent-systems, agentic-workflow, guardrails), `prompt-engineering` (system-prompts), `shared` (component-model.md) | Patterns for orchestrating the sub-flow and authoring specialist prompts |
| **IaC Impact** | None | Framework tooling feature — no infrastructure |

**Why This Matters:**

- **Location** → Design phase uses correct project structure, prevents misplaced files
- **KB Domains** → Design phase pulls correct patterns from `.claude/kb/`
- **IaC Impact** → Triggers infrastructure planning, avoids "works locally" failures

---

## Data Contract (if applicable)

N/A — framework tooling feature (AgentSpec developing AgentSpec); no data pipelines, sources, or SLAs involved.

---

## Assumptions

Assumptions that if wrong could invalidate the design:

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | The generated router inventory (`routing.json` + frontmatter) is a reliable availability oracle — frontmatter quality is high enough for domain matching | False negatives create duplicate specialists; false positives delegate to a weak match — would need richer matching heuristics or metadata | [ ] |
| A-002 | The `component-model` gate + ship checklist is a sufficient quality bar for run-generated specialists without human review | Low-quality specialists degrade build output — would pull judge/eval scoring back into scope | [ ] |
| A-003 | Specialists can be effective with `kb_domains: []` in domains that have no KB | Generated-specialist output quality too low in un-KB'd domains — would need KB pre-building or auto-creation (currently out of scope) | [ ] |
| A-004 | Mid-run authoring time fits within autopilot phase budgets | Design-phase gate timeouts in autonomous runs — retry/abort budgets would need tuning | [ ] |
| A-005 | Gaps are overwhelmingly detectable at design time from the file manifest; build-time drift is the exception | The safety net would carry most of the load, inverting the design-first sensor emphasis | [ ] |

**Note:** Validate critical assumptions before DESIGN phase. Unvalidated assumptions become risks.

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Specific failure mode (silent degradation to `(general)` or mid-build failure), specific victim (autonomous runs), specific cause (no gap detection) |
| Users | 3 | Two personas with concrete pain points, primary/secondary split explicit |
| Goals | 3 | MoSCoW-classified, each tied to a concrete workflow hook point |
| Success | 2 | Criteria are binary-testable, but "a domain is covered by an agent" lacks formal match semantics — the matching threshold is a Design-phase decision (ADR candidate) |
| Scope | 3 | Five explicit exclusions, all user-ratified; constraints enumerate the binding invariants |
| **Total** | **14/15** | |

**Scoring Guide:**
- 0 = Missing entirely
- 1 = Vague or incomplete
- 2 = Clear but missing details
- 3 = Crystal clear, actionable

**Minimum to proceed: 12/15**

---

## Open Questions

None blocking — ready for Design. One decision is explicitly delegated to Phase 2:

- **Match semantics (ADR candidate):** what precisely constitutes a router match for a task domain (exact `kb_domains` hit? description keyword coverage? confidence threshold?) — this is architecture, not requirements, and should be decided as an inline ADR in the DESIGN document.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-28 | define-agent | Initial version — extracted from user-ratified BRAINSTORM_SPECIALIST_AUTOPROVISION.md |
| 1.1 | 2026-07-28 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/ship .claude/sdd/features/DEFINE_SPECIALIST_AUTOPROVISION.md`
