---
name: auto
description: Execute the full SDD workflow autonomously from a single intent — gates decide, never a human (Autopilot)
---

# Auto Command

> One stated intent → self-answering Brainstorm → Define → Design → Build → Ship → open PR, with quality gates (not per-phase approval) deciding proceed, retry, or abort. Ends in an open PR or an actionable gap report — never a question.

## Usage

```bash
/auto "<intent>" [--no-brainstorm] [--no-judge] [--no-ship] [--no-pr] [--max-iterations N]
/auto FEATURE_NAME        # resume shorthand: continue an existing run by feature name
```

## Examples

```bash
# Lights-out: complete intent → open PR with archived docs
/auto "Add a --dry-run flag to scripts/rollout-agentspec.sh: print the file plan without copying, exit 0; covered by pytest cases for empty and populated targets"

# Vague intent → aborts at the clarity gate with a gap report naming what's missing
/auto "make the rollout script better"

# Skip Phase 0 (intent is already requirements-grade) and stop before archive
/auto "<intent>" --no-brainstorm --no-ship

# Resume after a killed session — regenerates nothing already approved
/auto "Add a --dry-run flag to scripts/rollout-agentspec.sh: ..."
/auto ROLLOUT_DRY_RUN
```

Headless (CI/cron) entrypoint — same policy, same terminal states: `scripts/autopilot.sh "<intent>" [flags]` (in this repo: `plugin-extras/scripts/autopilot.sh`).

---

## What happens

This command is a thin entrypoint; **every** proceed/retry/abort rule lives in the skill. If a behavior here ever seems to conflict with the skill, the skill wins.

1. **Load `.claude/skills/sdd-autopilot/SKILL.md`** and follow it end to end: intake (feature name derivation, resume matching), RUN REPORT creation, branch-first setup, the phase loop with Gates 0/L/J/B/S/PR, checkpoint commits, terminal status, notification.
2. **Parse flags** from the arguments (table below) and pass their policy meaning through — this command adds no interpretation of its own.
3. **Terminate** in exactly one of the skill's terminal states, with `AUTOPILOT_RUN_{FEATURE}.md` written in all of them:

| Terminal state | Meaning |
|----------------|---------|
| `✅ Success (PR: <url>)` | Full flow complete; PR open with code + docs + archive |
| `⚠ Partial Success` | Flow complete but a non-gate step failed (e.g., PR creation); report names the exact manual follow-up |
| `❌ Aborted (<gate>)` | A gate reached its terminal failure; report carries the gap report or violations |

## Flags

| Flag | Effect (semantics owned by the skill) |
|------|----------------------------------------|
| `--no-brainstorm` | Skip Phase 0 — intent feeds Define directly |
| `--no-judge` | Skip Gate J everywhere (recorded as skipped-by-flag) |
| `--no-ship` | Stop after Build (+ PR unless `--no-pr`); no archive |
| `--no-pr` | No PR; the branch is the deliverable |
| `--max-iterations N` | Run-wide cap on lint/judge regenerations |

## Invariants (from the skill — restated for visibility, not redefined)

- The run **never** asks the user anything; every gate resolves to proceed / retry-within-budget / abort-with-report.
- All retry budgets are bounded; every run terminates.
- Sensor unavailability (lint/judge exit ≥ 2 or CLI absent) is a **visible skip**, never an assumed PASS.
- Resume is the default: re-running `/auto` with the same intent (or the feature name) continues from the last approved gate.
- All writes happen on a `feat/auto-*` branch; `main` is never touched by a run.

---

## References

- Skill (single-source policy): `.claude/skills/sdd-autopilot/SKILL.md`
- Run report template: `.claude/sdd/templates/AUTOPILOT_RUN_TEMPLATE.md`
- Headless runner: `plugin-extras/scripts/autopilot.sh` (repo) / `${CLAUDE_PLUGIN_ROOT}/scripts/autopilot.sh` (plugin)
- Sensors: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` · `tools/spec-linter/USAGE.md` · `tools/spec-judge/USAGE.md`
- Phase entrypoints sequenced: `/brainstorm` · `/define` · `/design` · `/build` · `/ship` · `/create-pr`
- User guide: `docs/getting-started/autopilot.md`
