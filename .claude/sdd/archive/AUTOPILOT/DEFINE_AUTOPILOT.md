# DEFINE: Autopilot Mode

> A single stated intent executes the full SDD workflow autonomously — quality gates, not per-phase human approval, decide proceed or abort.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | AUTOPILOT |
| **Date** | 2026-07-27 |
| **Author** | define-agent |
| **Status** | ✅ Shipped |
| **Clarity Score** | 14/15 |

---

## Problem Statement

Running a feature through the SDD workflow requires manually invoking and supervising all five phase transitions (Brainstorm → Define → Design → Build → Ship); for well-specified intents this supervision adds no value — the user wants to state one intent and return to either an open PR or an actionable gap report, with the existing quality gates making every proceed/abort decision.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Matheus | AgentSpec author, daily SDD user | Babysits 5 phase transitions per feature, across multiple repos that vendor AgentSpec |
| AgentSpec plugin users | Data/software engineers using the SDD workflow | No lights-out option: even a launch-ready intent demands per-phase presence |

---

## Goals

What success looks like (prioritized):

| Priority | Goal |
|----------|------|
| **MUST** | `/auto "<intent>"` executes self-answering BRAINSTORM → DEFINE → DESIGN → BUILD → SHIP → open PR with zero human interaction when all gates pass |
| **MUST** | Hybrid escalation: intent gate (clarity < 12/15) aborts immediately with a gap report; generation gates auto-retry within bounded budgets (lint: 1 regeneration; judge: 1 refinement; build: retry_limit 3), then abort — the run NEVER waits for a human |
| **MUST** | `AUTOPILOT_RUN_{FEATURE}.md` written on every run (success or abort): gates evaluated, retries spent, autonomous decisions, gaps on abort |
| **MUST** | Gate policy defined once in the `sdd-autopilot` skill, consumed by both entrypoints (command and headless runner) |
| **MUST** | Resume by default: re-running `/auto` detects valid phase artifacts and restarts from the last approved gate |
| **MUST** | Judge gate (spec-judge) on by default after each lint PASS, per the ADR-003 `runs_after` contract; WARN feeds one bounded regeneration |
| **MUST** | Opt-out flags: `--no-brainstorm`, `--no-judge`, `--no-ship`, `--no-pr`, `--max-iterations N` |
| **MUST** | Headless runner (second entrypoint) completes the same flow from a non-interactive invocation (CI/cron capable) |
| **SHOULD** | End-of-run notification (best-effort by definition: a notification failure must never fail the run; the RUN REPORT is the authoritative record) |
| **COULD** | Token/cost accounting per phase in the RUN REPORT |

**Priority Guide:**
- **MUST** = MVP fails without this
- **SHOULD** = Important, but workaround exists
- **COULD** = Nice-to-have, cut first if needed

---

## Success Criteria

Measurable outcomes (must include numbers):

- [ ] A launch-ready intent reaches an open PR (code + archived docs) with **0** human interactions mid-run
- [ ] A vague intent aborts at the Define clarity gate (< 12/15) with a gap report naming each element scoring below 3 and what is missing — and creates **no** DESIGN/BUILD artifacts
- [ ] **100%** of runs (success or abort) produce `AUTOPILOT_RUN_{FEATURE}.md`
- [ ] After a killed session, re-running `/auto` resumes from the last approved gate, regenerating **0** already-approved artifacts
- [ ] The headless runner reaches the same terminal state as the interactive command for the same intent (validated with the canonical test pair)
- [ ] Gate policy exists in exactly **1** file (`sdd-autopilot` SKILL.md); the runner contains **0** duplicated policy rules
- [ ] All retry budgets are bounded: every run terminates (no infinite regeneration loops)

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Happy path (lights-out) | A complete, launch-ready intent | `/auto "<intent>"` | All phases execute with zero interaction; PR open; docs archived; RUN REPORT shows every gate PASS |
| AT-002 | Vague intent (fail-fast) | An intent missing users and success criteria | `/auto "<intent>"` | Run aborts at the clarity gate; gap report names the sub-12 elements; no DESIGN/BUILD artifacts exist |
| AT-003 | Lint FAIL with retry | A generated document fails spec-lint (exit 1) | Gate B evaluates | Exactly 1 regeneration attempt; on second FAIL the run aborts with the violation in the report; on PASS it proceeds |
| AT-004 | Linter unavailable | spec-lint returns exit 2 | Gate B evaluates | RUN REPORT records a VISIBLE skip; run proceeds; PASS is never assumed |
| AT-005 | Resume after kill | DEFINE and DESIGN exist with approved gates; session died during BUILD | `/auto` re-run for the same feature | Run resumes at BUILD; DEFINE/DESIGN not regenerated |
| AT-006 | Headless parity | Same intent as AT-001, invoked via the runner (no session) | Runner executes | Same terminal state as AT-001 (PR open, RUN REPORT written) |
| AT-007 | Judge WARN refinement | spec-judge returns WARN findings after lint PASS | Judge gate evaluates | Exactly 1 regeneration incorporating findings, then re-judge; run proceeds (WARN ceiling at standard tier) |
| AT-008 | Judge budget exhausted | judge exits 3 (daily ledger empty) | Judge gate evaluates | RUN REPORT records a visible skip; run continues; never blocks on budget |
| AT-009 | Opt-out flags | `/auto "<intent>" --no-judge --no-ship` | Run executes | Judge and Ship stages skipped; RUN REPORT records them as skipped-by-flag; run ends at PR |
| AT-010 | Notification failure | Notification mechanism unavailable at run end | Run terminates | Run outcome unchanged; RUN REPORT notes the failed notification attempt |

---

## Out of Scope

Explicitly NOT included in this feature:

- Multi-model ensemble judging (Judge V1+ territory, planned separately)
- Telemetry beyond the end-of-run notification (RUN REPORT is the observability surface)
- Flag System unification across the other phase commands (autopilot defines only its own flags)
- Hook-based orchestration (Approach B — rejected at brainstorm)
- Changes to the phase gates themselves (autopilot consumes existing sensors; it does not redefine clarity scoring, lint contracts, or judge tiers)

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Behavioral | The run must NEVER block waiting for human input | Every gate maps to proceed / retry-within-budget / abort-with-report — no "ask" branch |
| Technical | Gate sensors are the existing ones: clarity score, spec-lint (exit contract 0/1/2 — exit 2 is a VISIBLE skip, never assumed PASS), spec-judge tiers, build retry_limit, pre-ship checklist | Autopilot adds policy, not sensors; contract semantics owned by WORKFLOW_CONTRACTS.yaml are never reinterpreted |
| Technical | Judge runs only after lint PASS (ADR-003 `runs_after`); judge spend capped by the shared per-day ledger | Judge gate ordering fixed; exit 3 → visible skip |
| Technical | `scripts/` in this repo is NOT shipped in the plugin | Runner placement must be resolved at Design (plugin `scripts/` like init-workspace.sh, or repo-local + rollout) |
| Technical | Phase skills as written assume an interactive user (brainstorm mandates user questions; define asks below the gate) | The `sdd-autopilot` skill must define auto-mode conduct per phase (self-answer / abort instead of ask) — see A-002 |
| Resource | No new infrastructure; notification is best-effort | Notification failure never fails the run |
| Behavioral | All retry budgets bounded (lint 1, judge 1, build 3) | Guaranteed termination of every run |

---

## Technical Context

> Essential context for Design phase - prevents misplaced files and missed infrastructure needs.

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `.claude/commands/workflow/auto.md` · `.claude/skills/sdd-autopilot/` · `.claude/sdd/templates/AUTOPILOT_RUN_TEMPLATE.md` · runner location TBD (Design OQ-2) | Follows the phase trio pattern; command and skill ship in the plugin via build-plugin.sh |
| **KB Domains** | genai, prompt-engineering, python, testing, shared (component-model, conventions) | Multi-agent orchestration and guardrail patterns; runner implementation; gate-policy testing |
| **IaC Impact** | None | Framework tooling only; no infrastructure |

**Why This Matters:**

- **Location** → Design phase uses correct project structure, prevents misplaced files
- **KB Domains** → Design phase pulls correct patterns from `.claude/kb/`
- **IaC Impact** → Triggers infrastructure planning, avoids "works locally" failures

---

## Assumptions

Assumptions that if wrong could invalidate the design:

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | Model-computed clarity scoring is consistent enough to act as an autonomous go/no-go gate | Gate calibration needed against ground-truth feature docs before the score can abort runs credibly | [ ] |
| A-002 | Phase methodologies can run non-interactively via auto-mode overrides (brainstorm self-answers; define aborts instead of asking) | The `sdd-autopilot` skill must carry per-phase conduct overrides; if a phase cannot run unattended, it must be flagged out of the default chain | [ ] |
| A-003 | Headless `claude -p` invocations can load the plugin's skills/commands equivalently to an interactive session | Runner would need to inline phase prompts, increasing drift risk against the single-source policy | [ ] |
| A-004 | spec-linter and spec-judge CLIs are present in consuming repos (vendored/plugin) | Exit-2 visible-skip path degrades gracefully, but gate coverage silently narrows — RUN REPORT must make it loud | [ ] |
| A-005 | `OPENROUTER_API_KEY` is configured where the judge gate runs (default-on) | Judge gate degrades to visible skip (config-error path), matching the /define --judge error contract | [ ] |
| A-006 | Git state allows autonomous branch + PR creation at run end (/create-pr handles branching) | PR stage fails → run reports partial success with the manual step named | [ ] |

**Note:** Validate critical assumptions before DESIGN phase. Unvalidated assumptions become risks. A-002 and A-003 are the load-bearing ones — Design OQ-1 and OQ-2 resolve them.

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Specific pain (manual supervision of 5 transitions), specific owner, specific desired outcome (PR or gap report) |
| Users | 3 | Two personas with concrete pain points; primary user is also the author (fast validation loop) |
| Goals | 3 | Full MoSCoW with numeric budgets (retry 1/1/3), explicit defaults and opt-outs |
| Success | 2 | Criteria are testable, but gate calibration depends on ground-truth docs whose locations are still TBD (sample inventory) |
| Scope | 3 | Explicit out-of-scope list; boundaries between autopilot (policy) and sensors (existing gates) sharply drawn |
| **Total** | **14/15** | |

**Scoring Guide:**
- 0 = Missing entirely
- 1 = Vague or incomplete
- 2 = Clear but missing details
- 3 = Crystal clear, actionable

**Minimum to proceed: 12/15**

---

## Open Questions

Carried to Design (Phase 2) as design decisions — none block requirements:

1. **OQ-1 — Phase execution mechanics:** load phase skills sequentially in the main session vs. delegate each phase to its agent via Task (subagent-nesting implications: build-agent itself delegates). Resolves A-002.
2. **OQ-2 — Runner placement and distribution:** plugin `scripts/` (like init-workspace.sh) vs. repo-local + rollout script. Resolves A-003 in part.
3. **OQ-3 — Notification mechanism:** terminal, OS notification, or webhook — best-effort, must not fail the run.
4. **OQ-4 — Ship-then-PR ordering:** archive must land in the same PR as the code.

One requirements-level follow-up (does not block Design): collect the ground-truth feature-doc locations for gate calibration (Success score note).

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-27 | define-agent | Initial version from BRAINSTORM_AUTOPILOT.md |
| 1.1 | 2026-07-27 | ship-agent | Shipped and archived |

---

## Next Step

**Shipped:** archived in `.claude/sdd/archive/AUTOPILOT/` on 2026-07-27
