---
name: sdd-autopilot
description: |
  Single-source gate policy for Autopilot: one stated intent executes the full SDD workflow (self-answering Brainstorm → Define → Design → Build → Ship → PR) with quality gates, not per-phase human approval, deciding proceed, retry, or abort. Owns the complete autonomous-run methodology — the gate policy table and retry budgets, the per-phase auto-mode conduct overrides (self-answer instead of ask, abort instead of clarify), the run lifecycle (branch-first, checkpoint commits), the resume protocol, the RUN REPORT ledger obligations, abort semantics with gap reports, and the best-effort notification step. Consumed by both entrypoints: the /auto command (interactive) and plugin scripts/autopilot.sh (headless); neither restates a policy rule.
  Use when executing an autonomous SDD run — "/auto", "run the full workflow autonomously", "lights-out", "resume the autopilot run" — or when either entrypoint needs a gate's proceed/retry/abort rule.
  Do not use for a single supervised phase (use that phase's sdd-* skill), and do not use to change gate sensors — clarity scoring, lint contracts, and judge tiers are owned by their phases and by WORKFLOW_CONTRACTS.yaml; autopilot consumes them as-is.
---

# SDD Autopilot — autonomous full-workflow execution

One intent in; an open PR or an actionable gap report out. This skill is the **only** place autopilot policy lives: the `/auto` command (interactive) and `scripts/autopilot.sh` (headless) both execute this file and add no rules of their own. Autopilot adds **policy, not sensors** — every gate below consumes an existing sensor whose contract is owned elsewhere (`WORKFLOW_CONTRACTS.yaml`, `${CLAUDE_PLUGIN_ROOT}/tools/spec-linter/USAGE.md`, `${CLAUDE_PLUGIN_ROOT}/tools/spec-judge/USAGE.md`) and never reinterprets a verdict.

## The non-blocking invariant

**A run NEVER waits for a human.** Every gate resolves to exactly one of: proceed, retry-within-budget, or abort-with-report. There is no "ask" branch anywhere in this skill; `AskUserQuestion` is forbidden for the entire run. Every retry budget is finite, so every run terminates.

## Run lifecycle

```text
1. INTAKE     Derive {FEATURE} from the intent (SCREAMING_SNAKE_CASE, stable for
              the same intent). Freeze that value for the entire run. Parse flags.
              Check for an existing run (Resume).
2. OPEN       Create .claude/sdd/reports/AUTOPILOT_RUN_{FEATURE}.md from
              ${CLAUDE_PLUGIN_ROOT}/sdd/templates/AUTOPILOT_RUN_TEMPLATE.md — Status: In Progress,
              intent verbatim, flags, branch. If on the default branch, create and
              switch to feat/auto-{feature-kebab}; otherwise reuse the current branch.
3. PHASES     BRAINSTORM → DEFINE → DESIGN, each as:
                 load the phase's sdd-* skill → apply the conduct override below →
                 write the artifact → Gate L → Gate J → ledger rows →
                 checkpoint commit "auto({FEATURE}): {phase} complete"
              DEFINE additionally passes Gate 0 immediately after scoring.
4. BUILD      Load sdd-build; execute under its own decide-never-ask policy
              (delegation, per-file retry_limit 3). Then Gate B. Checkpoint commit.
5. SHIP       Load sdd-ship. Gate S (pre-ship checklist). Archive. Final commit.
6. PR         /create-pr. URL into the report. (Skipped stages per flags.)
7. CLOSE      Terminal status into the report; delete .autopilot/ scratch;
              notification step (best-effort).
```

**Artifact identity invariant:** `{FEATURE}` is derived exactly once at INTAKE and
never re-derived by a later phase. DEFINE, DESIGN, BUILD_REPORT, and AUTOPILOT_RUN
must therefore share the identical suffix:

```text
.claude/sdd/features/DEFINE_{FEATURE}.md
.claude/sdd/features/DESIGN_{FEATURE}.md
.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
.claude/sdd/reports/AUTOPILOT_RUN_{FEATURE}.md
```

Before each phase writes its artifact, reject any proposed filename whose suffix
differs from the frozen `{FEATURE}`. A mismatch is an orchestration error: record
it and abort rather than creating a second feature identity.

**Context discipline (protocol obligation):** the loop carries forward only artifact paths and gate results. Each phase re-reads its input document from disk; never paste a prior phase's document body into the running context beyond what that phase's skill itself reads.

## Gate policy

| Gate | Sensor | PASS | Recoverable failure | Budget | Terminal failure | Sensor unavailable |
|------|--------|------|--------------------|--------|------------------|--------------------|
| **0 — Intent** | clarity score (sdd-define) | ≥ 12/15 → proceed | none — fail-fast | 0 | < 12/15 → ABORT with gap report | n/a (model-computed) |
| **L — Lint** | `${CLAUDE_PLUGIN_ROOT}/tools/spec-linter/spec-lint <artifact> --phase <phase>` exit code | 0 → proceed | exit 1 → regenerate the document once with the violations in context, re-lint | 1 per document | second exit 1 → ABORT, violations in report | exit 2, or CLI not executable → VISIBLE SKIP row, proceed — never assume PASS |
| **J — Judge** | `${CLAUDE_PLUGIN_ROOT}/tools/spec-judge/spec-judge <artifact> --spec <ephemeral spec> --tier standard` exit code | 0 with PASS → proceed | 0 with WARN → one refinement incorporating every finding verbatim, re-judge, then proceed regardless (standard tier is WARN-capped by construction) | 1 per document | none reachable at standard tier | exit 2 (config) / 3 (budget) / 4 (network), or CLI not executable → VISIBLE SKIP row with the code named, proceed |
| **P — Provision** | specialist-autoprovision citation check after `scripts/generate-agent-router.py` regeneration (sub-flow owned by that skill; sensor contract: the `create-agent` parser contract) | new component citable in the oracle, core checklist items pass → proceed | authoring/validation failure → regenerate the component once with the violations in context | 1 per gap | budget exhausted → ABORT, gap report names the domain, attempts, failing checks | script not executable / oracle unreadable → VISIBLE SKIP row, fall back to `(general)` + WARN — never assume PASS |
| **B — Build** | sdd-build per-file verification + BUILD_REPORT completeness | report shows 100% tasks complete, tests passing | per-file fix-and-retry (sdd-build owns it) | 3 per file | incomplete report after retries → ABORT, failed tasks listed | n/a |
| **S — Ship** | pre-ship checklist (`WORKFLOW_CONTRACTS.yaml` → `ship.pre_ship_checklist`) | all 4 items pass | none | 0 | any unmet item → ABORT, item named | n/a |
| **PR** | `/create-pr` outcome | PR URL returned | none | 0 | failure → terminal status **⚠ Partial Success**, exact manual command in report | n/a |

Gate ordering within a document phase is fixed: **Gate L, then Gate J** — the judge runs only after a lint PASS (ADR-003 `runs_after`; never on a structural FAIL, and not after a Gate L visible skip — a skipped lint is not a PASS, so Gate J records `SKIPPED (no lint PASS)` and the run proceeds).

`--max-iterations N` caps the **run-wide sum** of Gate L + Gate J regenerations (default: the per-gate budgets, i.e. up to 2 per document). When the cap is hit, the next recoverable failure becomes terminal: ABORT with budget accounting.

### Gate L procedure

```bash
LINTER="${CLAUDE_PLUGIN_ROOT}/tools/spec-linter/spec-lint"
if [[ ! -x "$LINTER" ]]; then
  GATE_L="SKIP:unavailable"
else
  "$LINTER" "$ARTIFACT" --phase "$PHASE" \
    --contracts-file ${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml
  case $? in
    0) GATE_L="PASS" ;;
    1) GATE_L="FAIL" ;;
    2) GATE_L="SKIP:exit2" ;;
  esac
fi
```

Brainstorm has no `required_sections` today, so its Gate L lands on exit 2 by design — one more visible skip, not an error.

### Gate J procedure (ephemeral conformance spec)

The judge needs a spec; phase documents carry no frontmatter, so the loop materializes one per artifact:

```bash
SPEC_DIR=".claude/sdd/reports/.autopilot/${FEATURE}"
mkdir -p "$SPEC_DIR"
cat > "${SPEC_DIR}/spec_${PHASE}.yaml" <<EOF
name: autopilot-${PHASE}-conformance
intent: |
  ${INTENT}
  Phase purpose: ${PHASE_PURPOSE}          # the phase's purpose line from WORKFLOW_CONTRACTS.yaml
output_contract:
  required_fields: [${PHASE_REQUIRED_SECTIONS}]   # that phase's required_sections list
EOF

${CLAUDE_PLUGIN_ROOT}/tools/spec-judge/spec-judge "$ARTIFACT" --spec "${SPEC_DIR}/spec_${PHASE}.yaml" --tier standard
```

Standard tier only. Selecting a FAIL-eligible tier is a policy change, not a consumer option — see the boundary in the frontmatter. WARN findings feed exactly one refinement; the refined document is re-linted (a refinement can break structure) before the single re-judge. Re-lint after refinement draws from the same Gate L budget; if it is spent, a lint FAIL here is terminal.

The `.autopilot/` scratch directory is ephemeral: deleted at CLOSE, never committed, never archived.

## Auto-mode conduct overrides

Phase skills assume an interactive user. Under autopilot, these overrides apply — they change **conduct** (how the phase gets its answers), never the phase's output contract or quality gate:

| Phase | Interactive conduct | Autopilot override |
|-------|--------------------|--------------------|
| Brainstorm | One-question-at-a-time discovery; user validates approach | Self-answer every discovery question from KB + codebase evidence; record each Q&A with confidence and an explicit `[ASSUMED]` flag in the document; select the approach by the skill's own confidence matrix; YAGNI defers, never cuts a stated requirement; incremental validations recorded as self-validations |
| Define | Clarity < 12 → targeted `AskUserQuestion` rounds | Clarity < 12 → **Gate 0 ABORT**. No gap-filling questions, no padding entities to reach the gate — a fabricated requirement is worse than an abort |
| Design | Open questions may go back to the user | Every open question becomes an inline ADR with the chosen default and an `[ASSUMED]` marker; confidence < 0.80 on a decision adds a WARN row to the ledger |
| Build | Already decide-never-ask | Unchanged. CRITICAL-risk halt maps to ABORT-with-report (the halt is preserved; only the reporting surface changes) |
| Provisioning (within Design/Build) | The specialist-autoprovision layer fork may ask once at the component-model gate | Assume skill + thin executor, record `[ASSUMED]`; Gate P governs proceed/retry/abort |
| Ship | Minor issues → ask user (0.80 confidence branch) | Checklist is binding and mechanical: all 4 items pass → proceed; any unmet item → ABORT. The 0.80 "ask" branch maps to: record a WARN ledger row and proceed **iff** the checklist itself passes |

Every self-answered question and every `[ASSUMED]` marker is mirrored into the RUN REPORT's Autonomous Decisions table — the run is reviewable after the fact precisely because it never asked during.

## Resume protocol

Resume is the default; `--fresh` is not a flag (delete the RUN REPORT to force a fresh run — an explicit human act).

1. **Match:** on `/auto`, look for `AUTOPILOT_RUN_*.md` whose recorded intent matches the given intent (exact after whitespace normalization) or whose `{FEATURE}` equals the argument when the argument is a bare feature name.
2. **Replay:** read the Gate Ledger; find the last gate row with outcome PASS (or VISIBLE SKIP) per phase.
3. **Verify survivors:** for each phase at or before that point, confirm the artifact exists on disk. Artifact existence alone is NOT approval — the ledger row is; a document present on disk whose gate never passed is regenerated.
4. **Continue:** resume at the first phase without an approved gate, on the recorded branch, appending to the same report. Approved artifacts are never regenerated (0 regenerations of approved work).
5. A report whose Status is already terminal (`✅`/`⚠`/`❌`) plus an identical intent → do nothing except print the report path; state the run is closed. Re-opening a closed run is `/iterate` territory, not autopilot's.

## RUN REPORT obligations

- Created at OPEN, before the first gate can possibly fail — 100%-of-runs reporting is structural, not aspirational.
- Shape: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/AUTOPILOT_RUN_TEMPLATE.md`. Follow it; do not invent sections.
- **Gate Ledger:** one row per gate evaluation — including every retry, every visible skip (with the exit code or reason), every skipped-by-flag stage. Appended the moment the gate resolves, never batched at the end.
- **Autonomous Decisions:** every self-answered question, `[ASSUMED]` marker, and decision fork.
- **Gap report (on Gate 0 abort):** one row per clarity element scoring < 3 — the element, its score, and precisely what information is missing to raise it.
- Terminal Status values: `✅ Success (PR: <url>)` · `⚠ Partial Success` · `❌ Aborted (<gate>)`.
- Never echo environment values or secrets; sensors are recorded as present/absent, keys are never printed.

## Flags (semantics — the command owns parsing)

| Flag | Policy meaning |
|------|----------------|
| `--no-brainstorm` | Skip Phase 0; intent feeds Define directly; ledger row `SKIPPED (flag)` |
| `--no-judge` | Gate J skipped everywhere; ledger rows `SKIPPED (flag)` — coverage narrowed visibly |
| `--no-ship` | Stop after BUILD (+ PR unless `--no-pr`); no archive; Gate S not evaluated |
| `--no-pr` | Terminal state after SHIP; report records the branch as the deliverable |
| `--max-iterations N` | Run-wide Gate L + Gate J regeneration cap (see Gate policy) |

## Notification step (best-effort by contract)

Fire-and-forget, after the terminal status is written — a notification failure changes nothing about the run outcome and becomes one ledger note:

1. **Terminal summary** — always, both entrypoints: terminal status, report path, PR URL if any.
2. **OS notification** — headless runner only (`osascript` on darwin, `notify-send` on linux, skip silently if absent).
3. **Webhook** — headless runner only, iff `AUTOPILOT_WEBHOOK_URL` is set: POST `{feature, status, pr_url, report_path}`, 10s timeout.

The RUN REPORT is the authoritative record; notifications are conveniences.

## Anti-patterns

| Never do | Why | Instead |
|----------|-----|---------|
| Ask the user anything mid-run | Breaks the non-blocking invariant | Decide per the conduct overrides; record the decision |
| Treat lint/judge exit ≥ 2 as PASS | Assumed verdicts poison every downstream phase | VISIBLE SKIP row; proceed with coverage narrowed loudly |
| Re-encode a gate rule in the command or runner | Two policies drift; parity dies | Both entrypoints execute this file |
| Regenerate an approved artifact on resume | Wastes the checkpoint; risks divergence from the approved state | Trust the ledger, verify existence, continue |
| Pad a DEFINE to clear Gate 0 | Fabricated requirements compound through four phases | Abort with a gap report naming what is missing |
| Run Gate J after a Gate L skip or FAIL | Violates ADR-003 `runs_after` | Judge only on a real lint PASS |
| Commit or archive `.autopilot/` scratch | Ephemeral working files in permanent history | Delete at CLOSE |

## References

- Entrypoints: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/auto.md` (interactive) · `plugin-extras/scripts/autopilot.sh` (headless; `scripts/autopilot.sh` in the installed plugin)
- Report template: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/AUTOPILOT_RUN_TEMPLATE.md`
- Sensor contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml` (`contract_enforcement`, `behavioral_enforcement`, `build.execution`, `ship.pre_ship_checklist`) · `${CLAUDE_PLUGIN_ROOT}/tools/spec-linter/USAGE.md` · `${CLAUDE_PLUGIN_ROOT}/tools/spec-judge/USAGE.md`
- Phase methodologies: `${CLAUDE_PLUGIN_ROOT}/skills/sdd-brainstorm|define|design|build|ship/SKILL.md`
- Provisioning methodology (Gate P's sub-flow): `${CLAUDE_PLUGIN_ROOT}/skills/specialist-autoprovision/SKILL.md`
- Design rationale: `.claude/sdd/features/DESIGN_AUTOPILOT.md` (Decisions 1–6)
