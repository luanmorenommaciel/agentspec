# Autopilot — User Guide

> State one intent, get back an open PR or an actionable gap report. No per-phase supervision, no mid-run questions.

---

## What Autopilot Is

`/auto "<intent>"` runs the full SDD workflow — Brainstorm → Define → Design → Build → Ship → open PR — from a single stated intent, with zero human interaction during the run. Quality gates (not you) decide whether each phase proceeds, retries within a bounded budget, or aborts.

**The non-blocking guarantee:** a run never asks you anything. There is no "ask" branch — every gate resolves to proceed, retry-within-budget, or abort-with-report, so every run is guaranteed to terminate.

```bash
/auto "<intent>" [--no-brainstorm] [--no-judge] [--no-ship] [--no-pr] [--max-iterations N]
/auto FEATURE_NAME        # resume shorthand: continue an existing run by feature name
```

| Terminal state | What you get |
|-----------------|---------------|
| `✅ Success (PR: <url>)` | Open PR with code, phase docs, and archive |
| `⚠ Partial Success` | Everything ran, but the PR step itself failed — the branch is the deliverable, with the exact manual command in the report |
| `❌ Aborted (<gate>)` | A gate hit its terminal failure — an actionable gap report or violation list, never a silent stop |

Good fits: features you'd normally walk through all 5 phases for, where the intent is already clear.
Skip it for: exploratory work where you want to steer each phase — use `/brainstorm`, `/define`, `/design`, `/build`, `/ship` directly instead.

---

## Writing a Launch-Ready Intent

### The intent gate

Before anything else runs, Define scores the intent against 5 elements — Problem, Users, Goals, Success, Scope — each 0–3. Gate 0 requires **≥ 12/15**. Below that, the run aborts immediately: no Design, no Build, nothing downstream.

### Good: launch-ready

```text
Add a --dry-run flag to scripts/rollout-agentspec.sh: print the file plan without
copying, exit 0; covered by pytest cases for empty and populated targets
```

This scores high because it names the problem (missing dry-run flag), a concrete target (the script and its users), a measurable success criterion (prints the plan, exits 0), and bounds scope with a test requirement.

### Vague: aborts at Gate 0

```text
make the rollout script better
```

No named problem, no measurable outcome, no scope boundary. `/auto` on this intent aborts at Gate 0 before Design ever runs.

### Example gap report

On a Gate 0 abort, the RUN REPORT's Gap Report table names exactly what to add — one row per element scoring below 3:

| Element | Score | What is missing |
|---------|-------|------------------|
| Problem | 1 | What "better" means — performance, error handling, output format? |
| Success | 0 | No measurable outcome — what does the script produce today that it wouldn't after the change? |
| Scope | 1 | No boundary — which parts of the script change, and what's explicitly out |

Fix the intent with the missing elements and re-run `/auto "<revised intent>"` — Define re-scores from scratch.

---

## Flags

Everything runs by default; every flag opts a stage out.

| Flag | Effect |
|------|--------|
| `--no-brainstorm` | Skip Phase 0 — intent feeds Define directly |
| `--no-judge` | Skip Gate J everywhere (recorded as skipped-by-flag) |
| `--no-ship` | Stop after Build (+ PR unless `--no-pr`); no archive; Gate S not evaluated |
| `--no-pr` | Stop after Ship; no PR — the branch is the deliverable |
| `--max-iterations N` | Run-wide cap on Gate L + Gate J regenerations (default: per-gate budgets, up to 2 per document) |

---

## Headless Usage (CI/cron)

Same policy, same terminal states, no open session required:

```bash
scripts/autopilot.sh "<intent>" [--no-brainstorm] [--no-judge] [--no-ship] [--no-pr] [--max-iterations N]
```

In the AgentSpec repo itself the script lives at `plugin-extras/scripts/autopilot.sh` (merged into `plugin/scripts/` at build time, alongside `init-workspace.sh`).

The runner is a policy-free wrapper: preflight checks (the `claude` CLI is on `PATH`, the working directory is a git repo), a single `claude -p '/auto "<intent>" <flags>'` invocation, then exit-code mapping read from the RUN REPORT's terminal status.

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AUTOPILOT_TIMEOUT_MIN` | `60` | Minutes before the `claude -p` invocation is killed by `timeout` |
| `AUTOPILOT_WEBHOOK_URL` | unset | Optional webhook — POSTs `{feature, status, pr_url, report_path}` on completion, 10s timeout, best-effort |
| `AUTOPILOT_LOG` | unset | Optional transcript tee — path to write the headless session output |

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Terminal status was Success |
| `1` | Terminal status was Aborted |
| `2` | Preflight or operational failure — `claude` CLI missing, not a git repo, or the terminal status could not be determined |
| `3` | Terminal status was Partial Success — the workflow completed, but a non-gate step such as PR creation failed |

Schedule `scripts/autopilot.sh "<intent>"` from cron or a CI job and branch on the exit code; the RUN REPORT and the PR (if any) are the artifacts to inspect afterward.

---

## Reading the RUN REPORT

Every run — success or abort — writes `.claude/sdd/reports/AUTOPILOT_RUN_{FEATURE}.md` from `AUTOPILOT_RUN_TEMPLATE.md`. It's created before the first gate can possibly fail, and it is the run's only state: resume replays it, an abort explains itself through it.

| Section | What it tells you |
|---------|-------------------|
| **Metadata** | Intent verbatim, flags, branch, current status |
| **Gate Ledger** | One row per gate evaluation — every retry, every visible skip (with the reason), every skip-by-flag, appended live as each gate resolves |
| **Phase Artifacts** | Document path, checkpoint commit, and gate summary per phase |
| **Autonomous Decisions** | Every self-answered question and `[ASSUMED]` marker, with confidence and rationale — this is why the run is reviewable despite never asking |
| **Retry & Budget Accounting** | Spend against the Gate L / Gate J / Build budgets and `--max-iterations` |
| **Gap Report** | Present only on a Gate 0 abort — see above |
| **Terminal Summary** | Phases completed, gates evaluated, PR URL or exact manual follow-up |

Start with the Gate Ledger if you're auditing what the run decided on your behalf; read Autonomous Decisions if you want to know *why*.

---

## Resuming a Run

Resume is the default — there is no `--fresh` flag.

```bash
/auto "<same intent>"     # matched after whitespace normalization
/auto FEATURE_NAME        # or resume by feature name
```

`/auto` looks for an existing `AUTOPILOT_RUN_*.md` matching the intent or feature name, replays the Gate Ledger to the last **approved** gate (a passed or visibly-skipped gate, not just a file that happens to exist on disk), and continues from the first phase without one — on the recorded branch, appending to the same report. Nothing already approved is regenerated.

If the matched report is already terminal (`✅`/`⚠`/`❌`), `/auto` does nothing but print the report path and state the run is closed — reopening a shipped run is `/iterate` territory, not autopilot's. To force a genuinely fresh run, delete the RUN REPORT first — an explicit human act, not a flag.

---

## Requirements and Degradation

Autopilot works best with:

- `tools/spec-linter/spec-lint` present (Gate L)
- `tools/spec-judge/spec-judge` present, and `OPENROUTER_API_KEY` set (Gate J)

Neither is required to run. When a sensor is missing or errors operationally, the run does **not** assume a pass — it proceeds with a **visible skip**, recorded in the Gate Ledger with the exit code or reason named. Coverage narrows loudly, never silently.

**Branch safety:** every run works on `feat/auto-{feature-kebab}`, created on the first run (or reused on resume). `main` is never touched by an autopilot run — a killed session leaves `main` clean and the branch holding every checkpoint commit made so far.

---

## Gate Reference

| Gate | Checks | Retry budget | Abort condition |
|------|--------|---------------|------------------|
| **0 — Intent** | Clarity score (Define) | none — fail-fast | < 12/15 → abort with gap report |
| **L — Lint** | `spec-lint` exit code | 1 regeneration per document | second lint FAIL → abort with violations listed |
| **J — Judge** | `spec-judge` exit code, standard tier (runs only after a Gate L PASS) | 1 refinement per document (WARN only) | none reachable — standard tier is WARN-capped by design |
| **B — Build** | Per-file verification + BUILD_REPORT completeness | 3 retries per file | incomplete report after retries → abort with failed tasks listed |
| **S — Ship** | Pre-ship checklist (4 items) | none | any unmet item → abort with the item named |
| **PR** | `/create-pr` outcome | none | failure → **Partial Success** (not an abort) with the manual command in the report |

Sensor unavailable (lint/judge CLI absent, or an operational exit code) is always a visible skip in the ledger, never a silent pass — see Requirements and Degradation above.

---

## E2E Validation

For releases touching autopilot, run the canonical fixture pair, then the induced-failure checklist.

### Canonical pair

```bash
# Expect: full run, open PR, RUN REPORT shows every gate PASS
/auto "$(cat tests/fixtures/autopilot/intent_complete.txt)"

# Expect: abort at Gate 0 with a gap report; no DESIGN/BUILD artifacts created
/auto "$(cat tests/fixtures/autopilot/intent_vague.txt)"
```

### Induced-failure checklist

| Condition | How | Expect |
|-----------|-----|--------|
| Judge budget exhausted | `JUDGE_BUDGET=0 /auto "<intent>"` | Gate J records a visible skip; run proceeds |
| Linter unavailable | temporarily rename `tools/spec-linter/spec-lint` | Gate L records a visible skip; run proceeds |
| Killed mid-Build | kill the session during Build, then re-run `/auto` for the same feature | Resume continues from Build without regenerating already-approved Brainstorm/Define/Design artifacts |

---

## References

- Policy (single source): `.claude/skills/sdd-autopilot/SKILL.md`
- Command: `.claude/commands/workflow/auto.md`
- Run report shape: `.claude/sdd/templates/AUTOPILOT_RUN_TEMPLATE.md`
- Headless runner: `plugin-extras/scripts/autopilot.sh` (repo) / `scripts/autopilot.sh` (installed plugin)
- Judge setup (for Gate J): `docs/getting-started/judge-setup.md`
