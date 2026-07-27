# BRAINSTORM: Autopilot Mode

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | AUTOPILOT |
| **Date** | 2026-07-27 |
| **Author** | brainstorm-agent |
| **Status** | ✅ Complete (Defined) |

---

## Initial Idea

**Raw Input:** "Eu sempre tenho que ficar fazendo brainstorming, define, design, build e ship manualmente. Eu queria, no início, passar apenas a intenção e aí tudo ser executado de forma automática. Quando a minha intenção está correta e tem todas as informações necessárias, todo o fluxo é executado automaticamente."

Translation: run the full SDD flow (Brainstorm → Define → Design → Build → Ship) autonomously from a single stated intent, with quality gates deciding proceed/abort instead of per-phase human approval.

**Context Gathered:**

- All five SDD phases follow the thin-command + skill + thin-agent trio; `WORKFLOW_CONTRACTS.yaml` v3.5.0 is the contract source of truth.
- The mechanical gate sensors an autopilot needs already exist: Define clarity score (≥ 12/15), spec-linter (ADR-002, exit codes 0/1/2, wired for Define/Design), spec-judge (ADR-003, prototype, bindings are specified targets), Build per-file verification with `retry_limit: 3`, and the pre-ship checklist.
- `.claude/sdd/features/` and `archive/` are empty — clean slate, no in-flight features.
- The user maintains multiple repos that vendor AgentSpec (rollout via `scripts/rollout-agentspec.sh`); this feature brings lights-out autonomy into AgentSpec itself.

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | `.claude/commands/workflow/` + `.claude/skills/` + headless runner | Command entrypoint, methodology skill, second entrypoint for CI/cron |
| Relevant KB Domains | genai, prompt-engineering, python, testing, shared/component-model | Multi-agent orchestration patterns, runner implementation, gate policy grounding |
| IaC Patterns | N/A (framework tooling, no infra) | Plugin distribution via `build-plugin.sh`; note `scripts/` is NOT shipped in the plugin |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Escalation policy when a quality gate fails mid-run? | **Hybrid: fail-fast + retry** — intent gate (clarity < 12) aborts immediately with a gap report; generation gates (lint/judge/build) auto-retry up to a bounded budget, then abort with a report. The run never waits for a human. | Defines the autopilot's character: fire-and-forget, management by exception. Intent is treated as source code — if it doesn't "compile", the error report says what to fix. |
| 2 | Where does a successful run END? | First chose "full cycle to Ship", then revised to **"Build + PR open"**, then (validation 1) reverted to **ship in-run by default** as part of the all-on-by-default decision. Final: DEFINE → DESIGN → BUILD → SHIP → PR. | Run ends with feature archived and PR open. Accepted trade-off: if PR review demands changes, the archived feature must be reopened/updated. |
| 3 | What to do with Brainstorm (Phase 0) in auto mode? | First chose "skip — intent goes straight to Define", then (validation 1) reverted: **self-answering Brainstorm runs by default**, assumptions documented in the BRAINSTORM doc. Opt-out via `--no-brainstorm`. | Auto Phase 0 explores KB + codebase and answers its own discovery questions; wrong assumptions propagate, so the doc must flag every assumption explicitly. |
| 4 | Available samples to ground the solution? | **Past feature docs** (DEFINE/DESIGN/BUILD_REPORT from completed features in the user's work repos). Exact locations to be collected at Define. | Ground truth for calibrating the clarity gate and for end-to-end autopilot test cases. |

**Minimum Questions:** 3 (met — 4 asked, plus scope and approach confirmations)

---

## Sample Data Inventory

> Samples improve LLM accuracy through in-context learning and few-shot prompting.

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | N/A | 0 | Example intents to be authored as test fixtures during Build |
| Output examples | User's work repos (paths TBD at Define) | TBD | Completed DEFINE/DESIGN/BUILD_REPORT docs from shipped features |
| Ground truth | Same as output examples | TBD | What a "good" intent must contain to produce docs of that quality |
| Related code | `.claude/skills/sdd-*/`, `tools/spec-linter/`, `tools/spec-judge/` | 8+ | Phase skills, gate engines, exit-code contracts to reuse |

**How samples will be used:**

- Past feature docs calibrate the clarity gate: reverse-engineer what a launch-ready intent contains.
- One complete intent and one vague intent become the canonical end-to-end test pair (must-launch / must-abort-with-gap-report).
- Existing phase skills and gate engines are the reused building blocks — the autopilot adds policy, not new sensors.

---

## Approaches Explored

### Approach A: Orchestrator command + `sdd-autopilot` skill ⭐ Recommended

**Description:** New `/auto "<intent>"` command (thin entrypoint) + new `sdd-autopilot` skill (gate policy, retry budgets, resume detection, run-report format). The command sequences the existing phases, evaluating gates mechanically between them (clarity score, spec-lint exit codes, build-report completeness).

**Pros:**
- Pure reuse — zero changes to phase agents/skills; sensors (Linter/Judger) already exist
- Follows the repo's component model exactly (command = sequencing, skill = methodology)
- Ships in the plugin like any other command

**Cons:**
- The run lives in a single Claude Code session; if the session dies, the run dies (mitigated by resume: phase artifacts in `features/` are the state)

**Why Recommended:** Confidence 0.95 — KB pattern + codebase match. The command/skill/agent trio is the pattern of all 5 phases, and `WORKFLOW_CONTRACTS.yaml` already formalizes the gates the orchestrator consumes.

---

### Approach B: Hook-based orchestration (event-driven)

**Description:** `Stop`/`PostToolUse` hooks detect phase completion and trigger the next phase automatically.

**Pros:**
- Decoupled; survives across turns

**Cons:**
- State machine hidden in hook config — hard to debug; long hook chains are brittle
- Plugin distribution complicates (hooks require user consent)
- No precedent in the repo (confidence 0.70)

---

### Approach C: External headless runner (fully lights-out)

**Description:** `autopilot` script invoking `claude -p` per phase, checking gates deterministically between invocations (linter exit codes evaluated by code, not by the model).

**Pros:**
- Runs in CI/cron with no open session — true lights-out
- Each phase gets clean context; gates checked deterministically outside the model

**Cons:**
- New infrastructure outside the plugin's current shape; API keys/cost
- Awkward interaction loop when a run aborts

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A **+** Approach C combined (both entrypoints in V0) |
| **User Confirmation** | 2026-07-27, during this session (A chosen first; C pulled into V0 at the YAGNI review) |
| **Reasoning** | User wants maximum autonomy in V0, including CI/cron capability. The gate policy is written ONCE in the `sdd-autopilot` skill and consumed by both entrypoints — the runner adds an invocation surface, not a second policy. Approach B rejected: fragility and debuggability. |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|----------------------|
| 1 | Hybrid escalation: fail-fast on the intent gate, bounded auto-retry on generation gates, never pause for a human | Preserves fire-and-forget; the run always terminates with either a PR or an actionable gap report | Pause-and-ask (breaks fire-and-forget); abort-always (wastes machine-fixable retries) |
| 2 | Everything ON by default; flags are opt-OUT (`--no-brainstorm`, `--no-judge`, `--no-ship`, `--no-pr`) | User explicitly chose maximum default autonomy over the defaults-follow-earlier-decisions reconciliation | Opt-in flags with lean defaults |
| 3 | Default run = self-answering BRAINSTORM → DEFINE → DESIGN → BUILD → SHIP → PR | Full cycle in one run; formally reverses the earlier "skip Phase 0" and "end at PR" answers (see revision trail in Q&A #2/#3) | Lean core with opt-in phases |
| 4 | RUN REPORT always written (success or abort) to `.claude/sdd/reports/AUTOPILOT_RUN_{FEATURE}.md` | The report is the run's output contract: gates evaluated, retries spent, autonomous decisions, gaps on abort | Silent success / error-only output |
| 5 | Gate policy single-sourced in `sdd-autopilot` skill; both entrypoints (command + runner) consume it | Policy written once — no drift between interactive and headless modes | Duplicating policy in the runner |
| 6 | Resume by default: detect valid existing artifacts, restart from last approved gate | Phase artifacts already persist; a dead session shouldn't cost completed phases | Always-fresh runs |
| 7 | Judge gate runs after each lint PASS (per ADR-003 `runs_after` rule), WARN feeds one regeneration | Behavioral check catches what structural lint can't; bounded to keep the run terminating | Judge-free V0 (proposed, overridden by user) |

---

## Features Removed (YAGNI)

> Honest record: 7 cuts were proposed at the YAGNI step; the user reviewed each cut's flow and pulled **all 7 into V0** (decision #2/#3 above). The surviving removals are below.

| Feature Suggested | Reason Removed | Can Add Later? |
|-------------------|----------------|----------------|
| Multi-model ensemble judging | Judge V1+ territory (already planned separately); V0 uses the existing spec-judge tiers | Yes |
| Telemetry beyond the end-of-run notification | No new infra beyond the notification mechanism; RUN REPORT is the observability surface | Yes |
| Flag System unification across other phase commands | Separate planned initiative; autopilot defines only its own flags | Yes |
| PostToolUse-hook automation (Approach B elements) | Rejected with Approach B — fragile, hard to debug | Yes |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|---------------|-----------|
| Run flow + gate policy + YAGNI cuts | ✅ | Asked to see each cut's flow; then pulled all 7 items into V0; then chose "all on by default" over the defaults+opt-in reconciliation (explicitly reversing 3 earlier answers) | Yes — flow rebuilt around all-on defaults with opt-out flags |
| Artifacts + command surface + open Design questions | ✅ | Approved as presented | No |

**Minimum Validations:** 2 (met)

---

## Suggested Requirements for /define

### Problem Statement (Draft)

Running a feature through the SDD workflow requires manually invoking and supervising each phase; the user wants to state a single intent and have the full flow execute autonomously, with the existing quality gates — not per-phase human approval — deciding whether to proceed or abort.

### Target Users (Draft)

| User | Pain Point |
|------|------------|
| Matheus (AgentSpec author, daily SDD user) | Babysits 5 phase transitions per feature across multiple vendored repos |
| Any AgentSpec plugin user | Same supervision cost; no lights-out option for well-specified features |

### Success Criteria (Draft)

- [ ] `/auto "<complete intent>"` reaches an open PR (with shipped/archived docs) with zero human interaction
- [ ] `/auto "<vague intent>"` aborts at the clarity gate with a gap report that names the missing information
- [ ] Every run (success or abort) writes `AUTOPILOT_RUN_{FEATURE}.md` with gates evaluated, retries spent, and autonomous decisions
- [ ] A killed session can be resumed: re-running `/auto` restarts from the last approved gate
- [ ] The headless runner completes the same flow from a non-interactive invocation (CI/cron capable)
- [ ] Gate policy exists in exactly one place (`sdd-autopilot` skill), consumed by both entrypoints

### Constraints Identified

- The run must NEVER block waiting for human input (hybrid escalation, decision #1)
- Gate sensors are the existing ones: clarity score, spec-lint (exit-code contract 0/1/2 — exit 2 is a VISIBLE skip, never an assumed PASS), spec-judge tiers, build retry_limit, pre-ship checklist
- Judge runs only after lint PASS (ADR-003 `runs_after` contract); judge cost bounded by the shared per-day ledger
- `scripts/` in this repo is not shipped in the plugin — runner placement must be resolved (plugin `scripts/` like `init-workspace.sh`, or repo-local + rollout)
- All retry budgets bounded — every run terminates

### Out of Scope (Confirmed)

- Multi-model ensemble judging (Judge V1+)
- Telemetry beyond end-of-run notification
- Flag System unification across other phase commands
- Hook-based orchestration

### Open Questions for Design (Phase 2)

1. Phase execution mechanics: load phase skills sequentially in the main session vs. delegate each phase to its agent via Task (subagent-nesting implications — build-agent itself delegates).
2. Headless runner placement and distribution (plugin `scripts/` vs. repo-local + rollout script).
3. Notification mechanism (terminal, webhook, OS notification) — best-effort, must not fail the run.
4. Ship-then-PR ordering details: archive lands in the same PR as the code.

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 4 discovery + 3 confirmation/validation |
| Approaches Explored | 3 (A selected + C pulled in; B rejected) |
| Features Removed (YAGNI) | 7 proposed → 0 sustained (all pulled into V0); 4 items remain out of scope |
| Validations Completed | 2 |
| Duration | ~1 session |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_AUTOPILOT.md`
