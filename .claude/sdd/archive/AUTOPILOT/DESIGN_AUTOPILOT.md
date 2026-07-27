# DESIGN: Autopilot Mode

> Technical design for implementing AUTOPILOT — a single stated intent executes the full SDD workflow autonomously, with quality gates (not per-phase human approval) deciding proceed or abort.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | AUTOPILOT |
| **Date** | 2026-07-27 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_AUTOPILOT.md](./DEFINE_AUTOPILOT.md) |
| **Status** | ✅ Shipped |
| **Design Confidence** | 0.95 (KB patterns found: genai agentic-workflow, state-machines, guardrails; agent matches found: shell-script-specialist, test-generator, code-documenter) |

---

## Architecture Overview

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                        AUTOPILOT SYSTEM OVERVIEW                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ENTRYPOINT A (interactive)          ENTRYPOINT B (headless, CI/cron)       │
│  /auto "<intent>" [flags]            plugin-extras/scripts/autopilot.sh     │
│         │                                    │                              │
│         │                                    │ preflight, then:             │
│         │                                    │ claude -p '/auto "<intent>"' │
│         ▼                                    ▼                              │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │              ORCHESTRATION LOOP (main session)                    │      │
│  │   policy loaded from .claude/skills/sdd-autopilot/SKILL.md        │      │
│  │                                                                   │      │
│  │  [git branch]                                                     │      │
│  │      │                                                            │      │
│  │      ▼         ┌── Gate L (lint, exit 2 = visible skip)           │      │
│  │  BRAINSTORM ───┤                                                  │      │
│  │  (self-answer) └── Gate J (judge, standard tier, WARN→1 refine)   │      │
│  │      │                                                            │      │
│  │      ▼                                                            │      │
│  │  DEFINE ──── Gate 0 (clarity < 12/15 → ABORT + gap report)        │      │
│  │      │       Gate L → Gate J                                      │      │
│  │      ▼                                                            │      │
│  │  DESIGN ──── Gate L (FAIL → 1 regen → FAIL → abort) → Gate J      │      │
│  │      │                                                            │      │
│  │      ▼                                                            │      │
│  │  BUILD ───── per-file verification (retry_limit 3, existing)      │      │
│  │      │       + BUILD_REPORT completeness check                    │      │
│  │      ▼                                                            │      │
│  │  SHIP ────── pre-ship checklist (any unmet item → abort + report) │      │
│  │      │                                                            │      │
│  │      ▼                                                            │      │
│  │  /create-pr ── PR = code + phase docs + archive (one branch)      │      │
│  │                                                                   │      │
│  │  every gate result appended to ──► AUTOPILOT_RUN_{FEATURE}.md     │      │
│  │  (the run's ONLY state: resume reads it, abort explains in it)    │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│         │                                                                   │
│         ▼                                                                   │
│  [notification: terminal always; OS notify / webhook best-effort]           │
│                                                                             │
│  SENSORS (existing, consumed not modified):                                 │
│  clarity score · tools/spec-linter/spec-lint (0/1/2)                        │
│  tools/spec-judge/spec-judge (0/1/2/3/4) · build retry_limit ·              │
│  pre-ship checklist (WORKFLOW_CONTRACTS.yaml)                               │
└────────────────────────────────────────────────────────────────────────────┘
```

The autopilot adds **policy, not sensors**: every proceed/retry/abort rule lives once in the `sdd-autopilot` skill; both entrypoints consume it. The orchestration pattern is the KB's Sequential chain (genai `patterns/agentic-workflow.md`) with gate checks as output rails between steps (genai `concepts/guardrails.md`) — a linear state machine whose persisted state is the RUN REPORT.

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| `/auto` command | ENTRYPOINT — flag parsing (`--no-brainstorm`, `--no-judge`, `--no-ship`, `--no-pr`, `--max-iterations N`), loads the skill, runs the loop | Markdown command (`.claude/commands/workflow/auto.md`) |
| `sdd-autopilot` skill | CAPABILITY — gate policy table, retry budgets, per-phase auto-mode conduct overrides, resume protocol, RUN REPORT obligations, abort semantics, notification step | Markdown skill (`.claude/skills/sdd-autopilot/SKILL.md`) |
| `AUTOPILOT_RUN_TEMPLATE.md` | RUN REPORT shape — metadata, gate ledger, autonomous decisions, retries spent, gap report (on abort), terminal state | Markdown template (`.claude/sdd/templates/`) |
| Headless runner | Second entrypoint — preflight, single `claude -p '/auto …'` invocation, exit-code mapping, OS/webhook notification. **Zero policy rules.** | Bash (`plugin-extras/scripts/autopilot.sh`, shipped in plugin `scripts/` by the existing build merge) |
| Gate sensors (existing) | clarity score (sdd-define), spec-lint, spec-judge, build retry_limit, pre-ship checklist | Consumed as-is; contracts owned by `WORKFLOW_CONTRACTS.yaml` |
| Phase skills (existing) | sdd-brainstorm/define/design/build/ship methodology | Loaded sequentially by the loop; conduct overridden per the autopilot skill's auto-mode table |

### Gate policy (normative summary — full table lives in the skill)

| Gate | Sensor | PASS | Recoverable failure | Budget | Terminal failure | Unavailable sensor |
|------|--------|------|--------------------|--------|------------------|--------------------|
| 0 — Intent | clarity score | ≥ 12/15 → proceed | none (fail-fast) | 0 | < 12/15 → ABORT + gap report naming each element < 3 | n/a (model-computed) |
| L — Lint | spec-lint exit code | 0 → proceed | 1 → regenerate once, re-lint | 1 | second exit 1 → ABORT with violations | exit 2 or CLI absent → VISIBLE SKIP, proceed (never assume PASS) |
| J — Judge | spec-judge exit code (standard tier, runs only after Gate L PASS) | 0/PASS → proceed | 0/WARN → 1 refinement incorporating findings, re-judge, then proceed regardless (WARN ceiling) | 1 | unreachable at standard tier by construction | exit 2/3/4 or CLI absent → VISIBLE SKIP, proceed |
| B — Build | per-file verification + BUILD_REPORT completeness | report 100% complete | per-file retries (existing retry_limit) | 3/file | incomplete report after retries → ABORT with failed tasks listed | n/a |
| S — Ship | pre-ship checklist | all 4 items pass | none | 0 | any unmet item → ABORT + item named | n/a |
| PR | /create-pr outcome | PR URL returned | none | 0 | failure → PARTIAL SUCCESS: run report names the manual step | n/a |

`--max-iterations N` caps the **sum** of regenerations across Gates L and J for the whole run (default: the per-gate budgets above, total 2 per document × 3 documents). Exhaustion → abort with report. Every budget bounded → every run terminates.

---

## Key Decisions

### Decision 1: Phases execute in the main session via sequential skill loading (resolves OQ-1, A-002)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-27 |

**Context:** The loop must run five phases. Options: delegate each phase to its phase agent via Task, or load each phase's skill sequentially in the orchestrating session.

**Choice:** The `/auto` command loads each `sdd-*` phase skill in sequence in the main session and executes it under the autopilot conduct overrides. No new `auto-agent` is created.

**Rationale:** `build-agent` delegates to specialists via Task. Claude Code subagents cannot spawn subagents — delegating the Build phase to `build-agent` via Task would strand its own delegation, silently degrading the highest-risk phase. Running in the main session preserves Build's full delegation map and keeps gate evaluation (Bash calls to spec-lint/spec-judge, exit-code branching) in the orchestrator's hands. Context growth across phases is mitigated by protocol: each phase re-reads its input artifact from disk and the loop carries forward only artifact paths and gate results; the headless entrypoint gets a fresh session per run by construction.

**Alternatives Rejected:**
1. Per-phase Task delegation to phase agents — rejected: subagent nesting breaks build-agent's specialist delegation; gate evaluation would happen inside subagents, fragmenting the policy.
2. New `auto-agent` executor — rejected: an agent is a subagent shell; same nesting problem, plus the component model gives sequencing to commands, methodology to skills — there is no execution identity left over to justify an agent.

**Consequences:**
- One long session per interactive run; context discipline (paths, not content) is a stated protocol obligation in the skill.
- Zero changes to the five phase agents/skills — pure reuse, as the brainstorm's Approach A promised.

---

### Decision 2: The headless runner is a policy-free wrapper around one `claude -p '/auto …'` invocation (resolves OQ-2, A-003)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-27 |

**Context:** The runner must reach the same terminal state as the interactive command (AT-006) while the gate policy exists in exactly one file (success criterion: "0 duplicated policy rules"). The brainstorm's Approach C sketched a phase-by-phase driver evaluating gates in bash — but that IS a second policy encoding. Placement is also constrained: repo `scripts/` is not shipped in the plugin; `plugin-extras/scripts/` is merged into `plugin/scripts/` by the existing build (like `init-workspace.sh`), with `chmod +x` already applied.

**Choice:** `plugin-extras/scripts/autopilot.sh` — preflight (claude CLI present, git repo, clean-enough tree), then a single `claude -p '/auto "<intent>" <flags>' --permission-mode acceptEdits` invocation, then exit-code mapping by reading the RUN REPORT's terminal state, then best-effort notification. All gate logic stays in the skill, exercised by the model inside that one invocation.

**Rationale:** Parity by construction — both entrypoints execute the identical command + skill path, so they cannot drift. The runner adds an invocation surface (CI/cron, no open session), not a second brain. Placement in `plugin-extras/scripts/` ships it to plugin users with zero build-script changes and stays invocable repo-locally for dogfooding and the vendored repos (rollout script picks it up like any plugin file).

**Alternatives Rejected:**
1. Phase-by-phase `claude -p` driver with bash gate evaluation — rejected: duplicates retry/abort policy in a second language; violates the single-source success criterion; drift guaranteed.
2. Repo `scripts/autopilot.py` + build-plugin.sh change — rejected: needs build modification and leaves plugin users without the runner until rollout; more moving parts for the same surface.

**Consequences:**
- The runner depends on A-003 (headless `claude -p` loads plugin commands/skills); the runner's preflight verifies the `/auto` command resolves and exits 2 with a clear message if not — making the assumption loud instead of latent.
- A hung session inside the single invocation is handled by the runner's `timeout` wrapper (configurable, default 60m), not by policy.

---

### Decision 3: Judge gate = spec-judge at standard tier against an ephemeral per-artifact conformance spec

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-27 |

**Context:** The DEFINE mandates the ADR-003 judge after each lint PASS. `spec-judge` judges an artifact against a source spec (`--spec` YAML, or the artifact's own frontmatter — which phase documents don't have). Something must supply the spec.

**Choice:** Before each judge call, the orchestrator materializes a minimal conformance spec YAML at `.claude/sdd/reports/.autopilot/{FEATURE}/spec_{phase}.yaml`: `intent` = the user's intent plus the phase's purpose line from `WORKFLOW_CONTRACTS.yaml`; `output_contract.required_fields` = that phase's `required_sections`. Invocation: `spec-judge <artifact> --spec <that yaml> --tier standard`. WARN → one refinement incorporating the findings verbatim, re-judge, then proceed (AT-007). Exit ≥ 2 → visible skip (AT-008).

**Rationale:** Standard tier is WARN-capped **by construction**, so the judge can never block an autopilot run — exactly the bounded-advisory role the DEFINE assigns it — while still exercising the real ADR-003 engine (fault-seeker + conformance-checker + arbiter) rather than the older V0 `judge.py`. The ephemeral spec reuses the engine's existing `derived_from_instance` contract source; no new sensor is built.

**Alternatives Rejected:**
1. V0 `scripts/judge.py` (the `--judge` flag backend) — rejected: DEFINE names spec-judge and its exit contract explicitly; V0 supersession is already a planned separate migration.
2. High-assurance tier — rejected: FAIL-eligible and dual-model; contradicts "run never blocks on judge" and burns the shared ledger ~2× faster.

**Consequences:**
- `.autopilot/` working dir is ephemeral (gitignored via the report dir convention; cleaned by ship).
- Judge spend stays under the existing shared per-day ledger; budget exhaustion (exit 3) narrows coverage visibly, never silently (A-005, AT-008).

---

### Decision 4: The RUN REPORT is the run's only state — created at start, appended per gate, read on resume

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-27 |

**Context:** Resume-by-default (MUST) needs persisted run state; the RUN REPORT (MUST, written on every run) needs the same facts. Two artifacts would drift.

**Choice:** `AUTOPILOT_RUN_{FEATURE}.md` is created at run start (intent verbatim, feature name, flags, branch) with `Status: In Progress`, and a Gate Ledger row is appended the moment each gate resolves. Resume: `/auto` with a matching intent (normalized) or explicit feature name finds the report, replays the ledger to the last approved gate, cheaply re-verifies surviving artifacts exist, and continues — regenerating nothing already approved (AT-005). Terminal states: `✅ Success (PR: <url>)`, `⚠ Partial Success`, `❌ Aborted (<gate>)`.

**Rationale:** Write-ahead ledger and report are the same document; a killed session loses at most the phase in flight because phase artifacts already persist in `features/` and each phase lands in a checkpoint commit (Decision 5). No hidden state files.

**Alternatives Rejected:**
1. Separate JSON state file + rendered report — rejected: two sources of truth for one run; the report can lag the state it narrates.
2. Stateless resume by artifact sniffing alone — rejected: artifact existence ≠ gate approval (a document that failed lint still exists on disk); the ledger records approval, files record content.

**Consequences:**
- The template must make ledger rows append-friendly (one row per gate evaluation, including retries and visible skips).
- 100%-of-runs reporting (success criterion) falls out structurally: the report exists before the first gate can fail.

---

### Decision 5: Branch-first run; Ship archives before /create-pr; one PR carries code + docs + archive (resolves OQ-4, A-006)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-27 |

**Context:** The archive must land in the same PR as the code, and an autonomous run must never dirty `main` with a partial feature.

**Choice:** At run start, if on the default branch, create `feat/auto-{feature-kebab}` (resume reuses it). Each completed phase is a checkpoint commit (`auto({feature}): {phase} complete — {gate summary}`). Order at the end of the run: BUILD verified → SHIP (archive + statuses to Shipped) → final commit → `/create-pr`. If PR creation fails (no `gh` auth, no remote), the run terminates as PARTIAL SUCCESS with the exact manual command in the report — never as a hard failure.

**Rationale:** Checkpoint commits make resume cheap and the run auditable per phase; branch-first isolates every autonomous write; ship-before-PR is the only ordering that satisfies "archive in the same PR" without a second PR or post-merge commit. The accepted trade-off from brainstorm Q2 stands: review-driven changes reopen the archived feature via `/iterate`.

**Alternatives Rejected:**
1. PR after Build, Ship after merge — rejected: archive lands outside the PR, violating OQ-4's constraint.
2. Single squash commit at the end — rejected: a killed run leaves nothing committed; resume loses its checkpoints.

**Consequences:**
- Runs are safe to kill at any point: `main` untouched, branch holds the checkpoints.
- The PR diff includes moved (archived) docs — larger diff accepted for a self-contained record.

---

### Decision 6: Tiered best-effort notification (resolves OQ-3)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-27 |

**Context:** End-of-run notification is a SHOULD; failure must never fail the run (AT-010).

**Choice:** Three tiers, all fire-and-forget: (1) terminal summary — always, both entrypoints; (2) OS notification — runner only, `osascript` on darwin / `notify-send` on linux, skipped if absent; (3) webhook — runner only, `curl -m 10` POST of `{feature, status, pr_url, report_path}` iff `AUTOPILOT_WEBHOOK_URL` is set. Every tier is `|| true`; a failed attempt becomes one line in the RUN REPORT.

**Rationale:** Zero new infrastructure, degrades to the report (the authoritative record by DEFINE), covers laptop and CI cases.

**Alternatives Rejected:**
1. Notification as a blocking step with retries — rejected: inverts the SHOULD/best-effort contract.
2. Claude-side webhook call in the command — rejected: network side-effects belong in the runner's controlled shell, not in the model loop.

**Consequences:**
- Interactive `/auto` users get tier 1 only — acceptable: they have a terminal open by definition.

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `.claude/skills/sdd-autopilot/SKILL.md` | Create | Gate policy table, retry budgets, per-phase auto-mode conduct overrides, resume protocol, RUN REPORT obligations, notification step | (general) | None |
| 2 | `.claude/sdd/templates/AUTOPILOT_RUN_TEMPLATE.md` | Create | RUN REPORT shape: metadata, gate ledger, autonomous decisions, gap report, terminal state | (general) | None |
| 3 | `.claude/commands/workflow/auto.md` | Create | `/auto` entrypoint: flag table, skill loading, orchestration sequencing | (general) | 1, 2 |
| 4 | `plugin-extras/scripts/autopilot.sh` | Create | Headless runner: preflight, single `claude -p` invocation, timeout, exit mapping, OS/webhook notification | @shell-script-specialist | 1, 3 |
| 5 | `tests/fixtures/autopilot/intent_complete.txt` + `intent_vague.txt` | Create | Canonical test pair (must-launch / must-abort-with-gap-report) | @test-generator | None |
| 6 | `tests/test_autopilot_runner.py` | Create | Runner unit tests: arg parsing, preflight failures, exit mapping via a stubbed `claude` on PATH, notification no-fail | @test-generator | 4, 5 |
| 7 | `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Modify | Additive `autopilot:` block (entrypoints, RUN REPORT artifact, gate-policy pointer to the skill); version → 3.6.0 | (general) | 1, 3 |
| 8 | `docs/getting-started/autopilot.md` | Create | User guide: flags, headless usage, resume, reading the RUN REPORT (mirrors `judge-setup.md` shape) | @code-documenter | 3, 4 |
| 9 | `docs/reference/README.md` | Modify | Catalog entries: `/auto` command, `sdd-autopilot` skill | @code-documenter | 3 |
| 10 | `CLAUDE.md` | Modify | SDD commands table (+ `/auto`), skills inventory line, repository structure notes | (general) | 3 |
| 11 | `CHANGELOG.md` | Modify | Unreleased entry for Autopilot V0 | (general) | 1–10 |

**Total Files:** 11 (7 create, 4 modify)

---

## Agent Assignment Rationale

> Agents discovered from `.claude/agents/**/*.md` — Build phase invokes matched specialists.

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| @shell-script-specialist | 4 | Production-grade bash: strict mode, preflight checks, cross-platform notification, timeout handling — exactly its charter |
| @test-generator | 5, 6 | pytest suites with fixtures; the stubbed-`claude` PATH technique matches its fixture/mocking remit |
| @code-documenter | 8, 9 | User-facing docs and catalog entries |
| (general) | 1, 2, 3, 7, 10, 11 | Markdown command/skill/template authoring has no specialist agent; conventions come from the repo-local `create-skill` skill and the component model, executed directly |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md` (58 agents, 8 categories)
- Matched by: file type (`.sh` → shell specialist, `test_*.py` → test generator, `docs/` → documenter), purpose keywords, KB domains

---

## Code Patterns

### Pattern 1: Gate L evaluation — exit-code branching exactly as the contract owns it

```bash
# Inside the orchestration loop (skill-defined; executed via Bash tool).
# Never reinterpret verdicts; exit 2 is a VISIBLE skip, never an assumed PASS.
LINTER="tools/spec-linter/spec-lint"
if [[ ! -x "$LINTER" ]]; then
  echo "GATE L: SKIP (linter unavailable at $LINTER)"   # → ledger row: VISIBLE SKIP
else
  "$LINTER" "$ARTIFACT" --phase "$PHASE" \
    --contracts-file .claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml
  case $? in
    0) echo "GATE L: PASS" ;;
    1) echo "GATE L: FAIL" ;;   # policy: 1 regeneration, re-lint; second FAIL → abort
    2) echo "GATE L: SKIP (exit 2 — operational)" ;;
  esac
fi
```

### Pattern 2: Gate J — ephemeral conformance spec + standard-tier judge

```bash
SPEC_DIR=".claude/sdd/reports/.autopilot/${FEATURE}"
mkdir -p "$SPEC_DIR"
cat > "${SPEC_DIR}/spec_${PHASE}.yaml" <<EOF
name: autopilot-${PHASE}-conformance
intent: |
  ${INTENT}
  Phase purpose: ${PHASE_PURPOSE_FROM_CONTRACTS}
output_contract:
  required_fields: [${PHASE_REQUIRED_SECTIONS}]
EOF

tools/spec-judge/spec-judge "$ARTIFACT" --spec "${SPEC_DIR}/spec_${PHASE}.yaml" --tier standard
case $? in
  0) echo "GATE J: PASS/WARN" ;;          # WARN findings → 1 refinement, re-judge, proceed
  2|3|4) echo "GATE J: SKIP (exit $?)" ;; # config/budget/network — visible skip, proceed
esac
```

### Pattern 3: Runner skeleton — zero policy, one invocation, best-effort notification

```bash
#!/usr/bin/env bash
set -euo pipefail

INTENT="${1:?usage: autopilot.sh \"<intent>\" [passthrough flags]}"; shift || true
TIMEOUT_MIN="${AUTOPILOT_TIMEOUT_MIN:-60}"

command -v claude >/dev/null || { echo "ERROR: claude CLI not found" >&2; exit 2; }
git rev-parse --git-dir >/dev/null 2>&1 || { echo "ERROR: not a git repository" >&2; exit 2; }

timeout "${TIMEOUT_MIN}m" claude -p "/auto \"${INTENT}\" $*" \
  --permission-mode acceptEdits 2>&1 | tee -a "${AUTOPILOT_LOG:-/dev/null}"

REPORT="$(ls -t .claude/sdd/reports/AUTOPILOT_RUN_*.md 2>/dev/null | head -1)"
STATUS="$(grep -m1 '^| \*\*Status\*\*' "${REPORT:-/dev/null}" || echo "unknown")"

notify() {  # every tier fire-and-forget
  case "$(uname -s)" in
    Darwin) osascript -e "display notification \"${STATUS}\" with title \"Autopilot\"" || true ;;
    Linux)  command -v notify-send >/dev/null && notify-send "Autopilot" "$STATUS" || true ;;
  esac
  [[ -n "${AUTOPILOT_WEBHOOK_URL:-}" ]] && \
    curl -m 10 -fsS -X POST "$AUTOPILOT_WEBHOOK_URL" \
      -H 'Content-Type: application/json' \
      -d "{\"status\": \"${STATUS//\"/}\", \"report\": \"${REPORT}\"}" || true
}
notify

case "$STATUS" in
  *Success*) exit 0 ;;   # includes Partial Success — report names the manual step
  *Aborted*) exit 1 ;;
  *)         exit 2 ;;
esac
```

### Pattern 4: RUN REPORT gate ledger row (append-only, template-owned shape)

```markdown
| Gate | Phase | Attempt | Sensor result | Outcome | Timestamp |
|------|-------|---------|---------------|---------|-----------|
| L | define | 1 | spec-lint exit 0 | PASS | 2026-07-27T14:03Z |
| J | define | 1 | spec-judge WARN (B1 vagueness ×1) | REFINE (budget 1/1) | 2026-07-27T14:05Z |
| J | define | 2 | spec-judge PASS | PASS | 2026-07-27T14:08Z |
```

---

## Data Flow

```text
1. Intent received (/auto arg, or runner → claude -p)
   │
   ▼
2. Feature name derived (SCREAMING_SNAKE_CASE); RUN REPORT created (Status: In Progress);
   branch feat/auto-{kebab} created or reused; resume check replays the gate ledger
   │
   ▼
3. Per phase (BRAINSTORM → DEFINE → DESIGN): load phase skill under auto-mode
   conduct → write artifact → Gate L → Gate J → ledger rows → checkpoint commit
   (DEFINE additionally passes Gate 0 — clarity ≥ 12/15 or ABORT with gap report)
   │
   ▼
4. BUILD: sdd-build delegation loop (specialists via Task, retry_limit 3/file)
   → BUILD_REPORT completeness check → ledger → checkpoint commit
   │
   ▼
5. SHIP: pre-ship checklist → archive to .claude/sdd/archive/AUTOPILOT/ → statuses
   → final commit
   │
   ▼
6. /create-pr → PR URL into RUN REPORT → Status: ✅ Success (or ⚠ Partial / ❌ Aborted)
   │
   ▼
7. Notification tiers fire (best-effort) — report remains the authoritative record
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-----------------|----------------|
| Claude Code CLI (`claude -p`) | Subprocess from runner | User's existing session/API auth |
| spec-linter / spec-judge CLIs | Subprocess (exit-code contracts) | None (judge: `OPENROUTER_API_KEY` env) |
| OpenRouter (via spec-judge) | Indirect — sensor's own client | `OPENROUTER_API_KEY`; shared per-day ledger caps spend |
| GitHub (`gh` via /create-pr) | CLI subprocess | User's `gh auth` |
| Webhook endpoint (optional) | HTTP POST from runner | None (URL is the secret; env-provided) |
| OS notification (optional) | `osascript` / `notify-send` | None |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | Runner: preflight, arg parsing, exit mapping (stubbed `claude` on PATH), notification never fails run | `tests/test_autopilot_runner.py` | pytest + tmp PATH stubs | All runner branches (AT-006 mechanics, AT-010) |
| Static | Runner script quality | `plugin-extras/scripts/autopilot.sh` | `make lint` (shellcheck, `.shellcheckrc`) | 0 warnings |
| Contract | Skill/command/template ship in the plugin build | build output | `make build` + existing plugin tests | Files present in `plugin/` |
| E2E (scripted, model-dependent) | Canonical pair: complete intent → PR (AT-001); vague intent → clarity abort, no downstream artifacts (AT-002) | `tests/fixtures/autopilot/*.txt` + runner | documented procedure in `docs/getting-started/autopilot.md`; CI-optional job | Both terminal states reproduced |
| E2E gate matrix (manual, per release) | AT-003/004 (lint retry + skip), AT-005 (resume after kill), AT-007/008 (judge WARN + budget), AT-009 (flags) | checklist in doc #8 | Manual with induced conditions (e.g., `JUDGE_BUDGET=0` for AT-008, rename linter for AT-004, kill -9 mid-BUILD for AT-005) | Each AT observed once per release |

Acceptance-test coverage: AT-001..AT-010 all mapped above; deterministic paths automated (runner, build inclusion), model-dependent paths scripted or checklisted with induced-failure recipes — an honest split rather than fake automation of probabilistic behavior.

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| Clarity < 12/15 (Gate 0) | ABORT; gap report names each element < 3 and what's missing; no downstream artifacts | No (fail-fast) |
| spec-lint exit 1 | Regenerate document once with violations in context; re-lint | Yes (1) |
| spec-lint exit 2 / CLI absent | VISIBLE SKIP in ledger; proceed; never assume PASS | No |
| spec-judge WARN | One refinement incorporating findings; re-judge; proceed either way | Yes (1) |
| spec-judge exit 2/3/4 / CLI absent | VISIBLE SKIP (config / budget / network noted); proceed | No |
| Build task failure | Existing per-file retry_limit 3; then ABORT with failed tasks in report | Yes (3/file) |
| Pre-ship checklist unmet | ABORT; unmet item named in report | No |
| /create-pr failure | PARTIAL SUCCESS; exact manual command in report | No |
| Notification failure | One-line note in report; run outcome unchanged | No |
| Session killed mid-run | Nothing lost past last checkpoint commit; resume replays ledger, continues from last approved gate | n/a (resume) |
| `--max-iterations` exhausted | ABORT with budget accounting in report | No |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `--no-brainstorm` | flag | off (Phase 0 runs) | Intent goes straight to DEFINE |
| `--no-judge` | flag | off (judge on) | Skip Gate J everywhere (ledger: skipped-by-flag) |
| `--no-ship` | flag | off (ship runs) | Stop after BUILD + PR; no archive |
| `--no-pr` | flag | off (PR opens) | Stop after SHIP; no /create-pr |
| `--max-iterations` | int | per-gate budgets (L:1, J:1 per doc) | Run-wide cap on regenerations across Gates L+J |
| `AUTOPILOT_TIMEOUT_MIN` | env (runner) | `60` | `timeout` wrapper for the claude invocation |
| `AUTOPILOT_WEBHOOK_URL` | env (runner) | unset | Enables webhook notification tier |
| `AUTOPILOT_LOG` | env (runner) | unset | Tee target for the headless session transcript |
| `OPENROUTER_API_KEY`, `JUDGE_MODEL`, `JUDGE_BUDGET` | env (sensor-owned) | sensor defaults | Passed through untouched; owned by spec-judge |

---

## Security Considerations

- The runner invokes `claude -p` with `--permission-mode acceptEdits` — file edits inside the repo only; it never passes `--dangerously-skip-permissions`. Anything needing broader permissions aborts rather than escalates.
- All autonomous writes are branch-isolated (`feat/auto-*`); `main` is never committed to by a run.
- The RUN REPORT never echoes environment values — sensor availability is recorded as present/absent, keys are never printed.
- Webhook payload contains status + paths only, no document content; URL comes from the environment and is never written to the report.
- Judge spend is bounded by the existing shared per-day ledger; the autopilot adds no new spend path.

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Run record | `AUTOPILOT_RUN_{FEATURE}.md` — gate ledger (every evaluation, retry, visible skip), autonomous decisions, terminal state; the DEFINE-mandated observability surface |
| Logging | Runner tees the headless transcript to `AUTOPILOT_LOG` when set; checkpoint commits give per-phase git audit trail |
| Metrics | COULD-scope: per-phase token/cost rows in the RUN REPORT (template carries optional columns from day one so V1 fills them without a shape change) |
| Tracing | Git branch + ledger timestamps reconstruct the timeline; no external tracing infra (out of scope per DEFINE) |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-27 | design-agent | Initial version from DEFINE_AUTOPILOT.md; resolves OQ-1..OQ-4 as Decisions 1, 2, 5, 6 |
| 1.1 | 2026-07-27 | ship-agent | Shipped and archived |

---

## Next Step

**Shipped:** archived in `.claude/sdd/archive/AUTOPILOT/` on 2026-07-27
