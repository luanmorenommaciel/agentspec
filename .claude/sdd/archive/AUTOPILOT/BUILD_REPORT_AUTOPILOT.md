# BUILD REPORT: Autopilot Mode

> Implementation report for AUTOPILOT — `/auto` + headless runner executing the full SDD workflow autonomously under gate policy single-sourced in the `sdd-autopilot` skill.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | AUTOPILOT |
| **Date** | 2026-07-27 |
| **Author** | build-agent |
| **DEFINE** | [DEFINE_AUTOPILOT.md](../features/DEFINE_AUTOPILOT.md) |
| **DESIGN** | [DESIGN_AUTOPILOT.md](../features/DESIGN_AUTOPILOT.md) |
| **Status** | ✅ Shipped |

---

## Summary

| Metric | Value |
|--------|-------|
| **Tasks Completed** | 11/11 manifest files (+2 lint-wiring files, recorded as deviation) |
| **Files Created** | 8 (skill, template, command, runner, 2 fixtures, tests, user guide) |
| **Lines of Code** | ~1,300 new (incl. 279-line runner, 302-line test suite) + 6 files modified |
| **Build Time** | ~25m wall clock (2 delegation waves in parallel) |
| **Tests Passing** | 41/41 full suite (14 new) |
| **Agents Used** | 3 specialists + direct execution |

---

## Task Execution with Agent Attribution

| # | Task | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 1 | `.claude/skills/sdd-autopilot/SKILL.md` | (direct) | ✅ Complete | Single-source gate policy; registered live in-session on write |
| 2 | `.claude/sdd/templates/AUTOPILOT_RUN_TEMPLATE.md` | (direct) | ✅ Complete | Ledger doubles as resume state; optional token/cost columns for V1 |
| 3 | `.claude/commands/workflow/auto.md` | (direct) | ✅ Complete | Thin entrypoint; invariants restated, not redefined |
| 4 | `plugin-extras/scripts/autopilot.sh` | @shell-script-specialist | ✅ Complete | Zero policy verified; specialist fixed a skeleton bug (no-report path died under `set -euo pipefail`); 2 post-review fixes applied (direct) |
| 5 | `tests/fixtures/autopilot/intent_{complete,vague}.txt` | @test-generator | ✅ Complete | Canonical E2E pair |
| 6 | `tests/test_autopilot_runner.py` | @test-generator | ✅ Complete | 14 tests, stubbed `claude` on PATH, fully hermetic env |
| 7 | `WORKFLOW_CONTRACTS.yaml` → 3.6.0 | (direct) | ✅ Complete | Additive `autopilot:` block; YAML parse verified |
| 8 | `docs/getting-started/autopilot.md` | @code-documenter | ✅ Complete | Incl. E2E validation procedure + induced-failure checklist |
| 9 | `docs/reference/README.md` | @code-documenter | ✅ Complete | 32 commands / Workflow (8) / skills 16 core; counts reconciled |
| 10 | `CLAUDE.md` | (direct) | ✅ Complete | Counts, command table, key-files row, active-tasks row |
| 11 | `CHANGELOG.md` | (direct) | ✅ Complete | Unreleased → Added: Autopilot V0 |

---

## Agent Contributions

| Agent | Files | Specialization Applied |
|-------|-------|------------------------|
| @shell-script-specialist | 1 | Strict-mode bash, bash-3.2 (macOS) compatibility, `timeout`/`gtimeout` fallback, quote/backslash-safe prompt escaping, shellcheck-clean at `-S warning` |
| @test-generator | 3 | Hermetic pytest: from-scratch PATH/HOME, stubbed `claude` + `osascript`, subprocess exit-code contract coverage |
| @code-documenter | 2 | User-guide voice matched to `judge-setup.md`; catalog count reconciliation cross-checked against `build-plugin.sh` |
| (direct) | 7 | DESIGN patterns + component model (command=entrypoint, skill=policy) |

---

## Files Created

| File | Lines | Agent | Verified | Notes |
| ---- | ----- | ----- | -------- | ----- |
| `.claude/skills/sdd-autopilot/SKILL.md` | ~150 | (direct) | ✅ | Loads as a live skill; frontmatter description follows house Use-when/Do-not-use shape |
| `.claude/sdd/templates/AUTOPILOT_RUN_TEMPLATE.md` | 105 | (direct) | ✅ | Append-friendly gate ledger |
| `.claude/commands/workflow/auto.md` | 79 | (direct) | ✅ | Registered as /auto in-session |
| `plugin-extras/scripts/autopilot.sh` | 279 | @shell-script-specialist | ✅ | shellcheck clean; `--help` exit 0; ships as `plugin/scripts/autopilot.sh` |
| `tests/fixtures/autopilot/intent_complete.txt` | 1 | @test-generator | ✅ | Requirements-grade intent |
| `tests/fixtures/autopilot/intent_vague.txt` | 1 | @test-generator | ✅ | Not referenced by runner tests by design — clarity gating is model-side; reserved for the documented E2E procedure |
| `tests/test_autopilot_runner.py` | 302 | @test-generator | ✅ | 14/14 pass |
| `docs/getting-started/autopilot.md` | 203 | @code-documenter | ✅ | Gate reference + degradation contract |

**Files modified:** `WORKFLOW_CONTRACTS.yaml` (3.6.0), `docs/reference/README.md`, `CLAUDE.md`, `CHANGELOG.md`, `Makefile` + `.github/workflows/quality-checks.yml` (deviation, below).

---

## Verification Results

### Lint Check

```text
make lint → shellcheck -S warning (incl. plugin-extras/scripts/autopilot.sh): clean, 0 findings
```

**Status:** ✅ Pass

### Type Check

```text
N/A — no Python source changed; mypy not configured for this repo's test-only Python
```

**Status:** ⏭️ Skipped

### Tests

```text
python3 -m pytest tests/ -q → 41 passed in 4.04s (14 new in test_autopilot_runner.py; 27 pre-existing, no regressions)
```

| Test group | Result |
|------|--------|
| Help / argument validation (2) | ✅ Pass |
| Preflight failures ×3 | ✅ Pass |
| Status → exit-code mapping ×5 (success/partial/aborted/no-report/garbled) | ✅ Pass |
| Prompt construction: quote/backslash intents, flag passthrough (2) | ✅ Pass |
| Notifications: unreachable webhook never affects exit; URL never printed (2) | ✅ Pass |

**Status:** ✅ 41/41 Pass

### Plugin Inclusion (contract check from DESIGN testing strategy)

```text
make build → 58 agents / 32 commands / 17 skills / 24 KB domains; linter + judger bundled
plugin/commands/workflow/auto.md · plugin/skills/sdd-autopilot/SKILL.md ·
plugin/sdd/templates/AUTOPILOT_RUN_TEMPLATE.md · plugin/scripts/autopilot.sh — all present
```

**Status:** ✅ Pass

### Contracts YAML

```text
yaml.safe_load OK — version 3.6.0, autopilot block keys: command, gates_consumed, headless_runner, invariants, output, skill
```

**Status:** ✅ Pass

---

## Issues Encountered

| # | Issue | Resolution | Time Impact |
|---|-------|------------|-------------|
| 1 | DESIGN skeleton bug: `ls … | head -1` report lookup dies under `set -euo pipefail` when no report exists, making "no report" indistinguishable from "Aborted" | Found and fixed by @shell-script-specialist during build (`|| true` on the assignment); regression-covered by test case 9 | +0m (caught in delegation) |
| 2 | Test review surfaced: exit-code `case` matched the raw markdown row (`STATUS_LINE`) instead of the extracted value | Fixed (direct): `compute_exit_code` now matches `STATUS_VALUE`; suite re-run green | +2m |
| 3 | Test review surfaced: no stderr signal distinguishing "no report" from "garbled Status row" (both exit 2) | Fixed (direct): two distinct `WARNING:` stderr lines in `extract_status`; suite re-run green | +2m |
| 4 | `pytest` binary not on PATH in this environment (rtk hook quirk) | Ran via `rtk proxy python3 -m pytest` — pre-existing environment quirk, not a code issue | +1m |

---

## Autonomous Decisions

| # | Decision Point | Options Considered | Chose | Rationale |
|---|----------------|--------------------|-------|-----------|
| 1 | Runner not covered by `make lint` / CI shellcheck (both enumerate scripts by name; Makefile and workflow not in manifest) | (a) leave unlinted; (b) add to both lists | (b) — modified `Makefile` + `.github/workflows/quality-checks.yml` | DESIGN's testing strategy explicitly routes runner linting through `make lint`; without the entry the strategy is unsatisfiable. Smallest change honoring the DESIGN; recorded as deviation |
| 2 | Runner finding: no `--` separator — an intent starting with `-h` is swallowed by help parsing | (a) add `--` escape hatch; (b) accept and document | (b) accepted | Intents are natural-language sentences; a leading `-` is pathological. Smallest-correct-change principle; noted here for V1 |
| 3 | Runner finding: no `timeout`/`gtimeout` → unbounded run (stock macOS) | (a) bash-native watchdog (background sleep+kill); (b) keep designed warn-and-proceed | (b) kept | DESIGN Decision 2 explicitly specifies warn-and-run-without-timeout; a homegrown watchdog adds kill/cleanup complexity the design rejected |
| 4 | Docs written in parallel with the runner (doc agent started before runner existed) | (a) serialize; (b) parallelize against the contract-pinned interface | (b) | Flags/env/exit codes were fully pinned by DESIGN + skill + delegation prompt; verified afterward — no drift found |
| 5 | `/auto` resolution preflight implementation (DESIGN said "verify it resolves" without a mechanism) | file checks (repo path, `CLAUDE_PLUGIN_ROOT`, `~/.claude/plugins/*` glob) vs. a probe `claude -p` invocation | file checks | A probe invocation costs an API call and seconds; file existence is deterministic and free. Chosen by @shell-script-specialist, ratified on review |

---

## Deviations from Design

| Deviation | Reason | Impact |
|-----------|--------|--------|
| +2 modified files not in manifest: `Makefile`, `.github/workflows/quality-checks.yml` | Both enumerate shellcheck targets by explicit name; the DESIGN's "Static" test row (`make lint` covers the runner) is unsatisfiable without the entries | Runner continuously linted locally and in CI |
| Runner is 279 lines vs. the DESIGN's ~40-line skeleton | Production hardening: preflight functions, bash-3.2 compatibility, escaping, help text, warning paths — all within Decision 2's zero-policy constraint (verified: only branching on claude output is the 3-way status map) | None on architecture; behavior contract identical |

---

## Blockers (if any)

None.

---

## Acceptance Test Verification

Per the DESIGN's testing strategy, deterministic mechanics are automated; model-dependent gate behavior is deferred to the documented E2E procedure (`docs/getting-started/autopilot.md`) — an honest split, not fake automation.

| ID | Scenario | Status | Evidence |
|----|----------|--------|----------|
| AT-001 | Happy path lights-out → PR | ⏭ E2E procedure | Command+skill+gates+PR stage all in place; canonical fixture `intent_complete.txt` ready; run procedure documented |
| AT-002 | Vague intent → clarity abort + gap report | ⏭ E2E procedure | Gate 0 abort + gap-report shape defined in skill + template; fixture `intent_vague.txt` ready |
| AT-003 | Lint FAIL → 1 regen → abort | ⏭ E2E procedure | Policy encoded in skill Gate L (budget 1); induced-failure recipe documented |
| AT-004 | Linter unavailable → visible skip | ⏭ E2E procedure | `SKIP:unavailable` / `SKIP:exit2` ledger outcomes defined; recipe: rename spec-lint |
| AT-005 | Resume after kill | ⏭ E2E procedure | Resume protocol (ledger replay, artifact re-verify) in skill; recipe: kill mid-Build |
| AT-006 | Headless parity | ✅ Partial (mechanics) | 14 unit tests: preflight, single-invocation, exit mapping from RUN REPORT, flag passthrough — parity-by-construction argument holds (runner contains zero policy, verified by review) |
| AT-007 | Judge WARN → 1 refinement | ⏭ E2E procedure | Gate J procedure + budget in skill; standard tier WARN-capped |
| AT-008 | Judge budget exhausted → visible skip | ⏭ E2E procedure | Exit-3 → `SKIP` path in skill; recipe: `JUDGE_BUDGET=0` |
| AT-009 | Opt-out flags | ✅ Partial (mechanics) | Flag passthrough verified in unit test; `SKIPPED (flag)` ledger semantics in skill |
| AT-010 | Notification failure changes nothing | ✅ Pass | Unit-tested: unreachable webhook → exit code still maps from report; URL never printed |

---

## Performance Notes

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Full test suite | no regressions | 41/41, 4.04s | ✅ |
| Plugin build | all autopilot files ship | 4/4 present in `plugin/` | ✅ |
| Policy single-sourcing | 0 duplicated rules in runner | Verified by review: runner's only output-dependent branch is the terminal status map | ✅ |

---

## Final Status

### Overall: ✅ COMPLETE

**Completion Checklist:**

- [x] All tasks from manifest completed (11/11, +2 recorded deviations)
- [x] All verification checks pass (shellcheck, YAML, plugin inclusion)
- [x] All tests pass (41/41)
- [x] No blocking issues
- [x] Acceptance tests verified (deterministic: automated; model-dependent: E2E procedure documented per DESIGN)
- [x] Ready for /ship

---

## Next Step

**If Complete:** `/ship .claude/sdd/features/DEFINE_AUTOPILOT.md`
