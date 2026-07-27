---
name: rollout-agentspec
description: |
  Rolls out the current AgentSpec build to the vendored consuming repos by operating
  scripts/rollout-agentspec.sh through its safe sequence: fresh payload build, dry-run
  plan review, user-confirmed --apply with automatic backups, per-target verification,
  and rollback via backup stamps. Targets come from the gitignored
  .agentspec-rollout-targets file at the repo root — never hardcoded, never committed.
  Use whenever the user asks to roll out AgentSpec, update or upgrade the vendored
  installs, propagate agent/skill/KB changes to the target or consuming repos, sync
  AgentSpec into their other projects, or roll back a previous rollout. Do not use for
  publishing the plugin or marketplace release, and never copy files into target repos
  by hand — naive cp corrupts vendored installs; the script owns all writes.
---

# Rollout AgentSpec (vendored targets)

Some of the user's repos vendor AgentSpec directly inside their `.claude/` directory
(no plugin install). `scripts/rollout-agentspec.sh` is the only safe writer for those
installs: it replaces AgentSpec-owned paths with a scoped delete-then-copy and
preserves everything target-owned (SDD workspace, settings, target-only KB domains,
skills, and commands). A naive `cp -r` destroys that target-owned work — which is why
this skill never touches target repos directly and drives everything through the
script.

## When to use

- The user asks to roll out, propagate, or sync AgentSpec to the targets / consuming
  repos, or to upgrade the vendored installs.
- The user wants a recent AgentSpec change (agents, skills, KB, templates) available
  in their other projects.
- The user wants to undo a rollout — see Rollback below.

## Skip if

- The user wants to publish the plugin or marketplace release — that is the release
  flow (`build-plugin.sh` + version bump), not a rollout.
- The user wants to change *what* gets rolled out — payload contents are decided by
  the plugin build; fix them there, then roll out.

## The sequence

Run these steps in order. Each exists because the apply step rewrites files inside
other repositories — everything before it is what makes that safe.

1. **Preflight.** Confirm `.agentspec-rollout-targets` exists at the repo root
   (gitignored; one path per line, `#` comments, `~` expansion). If it is missing,
   ask the user for the target paths and write the file — never guess paths and never
   hardcode them in any committed file: this repo is public and target paths are
   machine-specific. Targets can also be passed as script arguments for a one-off.
2. **Fresh payload.** Run `make build` (or pass `--build` to the script). The rollout
   stages from `plugin/` — a stale payload silently ships stale components.
3. **Dry-run.** Run `scripts/rollout-agentspec.sh` with no flags (dry-run is the
   default). Read the whole plan, not just the tail — see "Reading the plan" below.
4. **Confirm.** Summarize the plan per target and get the user's go-ahead before
   `--apply`. If the user already said to apply in their request ("pode aplicar",
   "roll it out for real"), proceed without re-asking. The gate exists because some
   targets' `.claude` may be gitignored in *their* repo — the script's backup is
   their only safety net.
5. **Apply.** Run `scripts/rollout-agentspec.sh --apply`. Record the backup stamp the
   script prints (`~/.agentspec-rollout-backups/<stamp>/`).
6. **Verify and report.** Map the exit code (table below), name any skipped or failed
   targets and why, and hand the user the backup stamp plus the exact rollback
   command.

## Reading the plan

Three dry-run lines deserve attention; surface them instead of skimming past:

- `UNCLASSIFIED (preserved, review manually): <entry>` — an unknown top-level entry
  in a target's `.claude`. The script preserves it, but the user should know it exists.
- `kb/_index.yaml: would merge N target-only domains: <names>` — target-only KB
  domains that stay registered after the rollout. A `MERGE SKIPPED`/`VALIDATION
  FAILED` warning here means the target keeps its old index and new payload domains
  stay unregistered until fixed — report it loudly.
- `WARNING: no .claude directory — skipping <name>` — a wrong path or a repo that
  does not vendor AgentSpec; check the targets file.

## Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | All targets synced | Report the stamp and per-target summary |
| 1 | Partial — some target skipped/failed | Name which targets and why; the rest applied |
| 2 | Bad usage or environment | The error message says what; fix and rerun |

## Rollback

```bash
scripts/rollout-agentspec.sh --rollback --stamp <STAMP> [targets...]
```

Restores each target's `.claude` from `~/.agentspec-rollout-backups/<stamp>/`. The
stamp is printed at apply time; `ls ~/.agentspec-rollout-backups` lists what exists.

For full flags and the managed-path contract, run `scripts/rollout-agentspec.sh --help`.
