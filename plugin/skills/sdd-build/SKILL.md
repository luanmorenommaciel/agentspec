---
name: sdd-build
description: |
  Execution methodology for SDD Phase 3 (Build): turn a completed DESIGN into working,
  verified code. Covers KB-first knowledge resolution, task extraction from the file
  manifest, dependency ordering, specialist agent delegation (including the data
  engineering delegation map), per-file and full-run verification, recording autonomous
  decisions in the BUILD_REPORT, upstream status transitions, and the handoff to Phase 4.
  Use when asked to "execute the build", "implement from the design", or run "Phase 3"
  on a DESIGN_{FEATURE}.md. Not for creating the architecture itself — that is
  sdd-design — and not for archiving a finished feature — that is sdd-ship.
---

# SDD Build — Phase 3 Methodology

> The HOW of Phase 3: execute a completed DESIGN into working, verified code with
> on-the-fly task generation and specialist delegation. The executor is
> `build-agent` (`${CLAUDE_PLUGIN_ROOT}/agents/workflow/build-agent.md`); its non-negotiable
> policies — decide-never-ask and halt-only-on-CRITICAL-risk — govern every step
> below and are not restated here.

---

## Knowledge Architecture — KB-First Resolution

Follow this resolution order before and during every task. It is mandatory, not optional.

```text
┌─────────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE RESOLUTION ORDER                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. DESIGN LOADING (source of truth for implementation)             │
│     └─ Read: .claude/sdd/features/DESIGN_{FEATURE}.md               │
│     └─ Extract: File manifest, code patterns, agent assignments     │
│     └─ Load KB domains specified in design                          │
│                                                                      │
│  2. KB PATTERN VALIDATION (before writing code)                     │
│     └─ Read: ${CLAUDE_PLUGIN_ROOT}/kb/{domain}/patterns/*.md → Verify patterns    │
│     └─ Compare: DESIGN patterns vs KB patterns → Ensure alignment   │
│                                                                      │
│  3. AGENT DELEGATION (for specialized files)                        │
│     ├─ @agent-name in manifest → Delegate via Task tool             │
│     └─ (general) in manifest   → Execute directly from patterns     │
│                                                                      │
│  4. CONFIDENCE ASSIGNMENT                                            │
│     ├─ KB pattern + agent specialist    → 0.95 → Execute            │
│     ├─ KB pattern + general execution   → 0.85 → Execute with care  │
│     ├─ No KB pattern + agent specialist → 0.80 → Agent handles      │
│     └─ No KB pattern + general          → 0.70 → Verify after       │
│                                                                      │
│  5. DECISION FORKS                                                   │
│     └─ Resolve under the executor's decide-never-ask policy and     │
│        record per "Recording Autonomous Decisions" below.           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Execution Loop

### Step 1: Load Context

```markdown
Read(.claude/sdd/features/DESIGN_{FEATURE}.md)
Read(.claude/sdd/features/DEFINE_{FEATURE}.md)
Read(CLAUDE.md)
```

Extract from the DESIGN: the file manifest, code patterns, agent assignments, and
the KB domains to load.

### Step 2: Extract Tasks from the File Manifest

Convert the manifest to a task list — tasks are generated on-the-fly, not
pre-written:

```markdown
From DESIGN file manifest:
| File | Action | Purpose |

Generate:
- [ ] Create/Modify {file1}
- [ ] Create/Modify {file2}
- [ ] ...
```

### Step 3: Order by Dependencies

Analyze imports and dependencies to determine execution order:
config first → utilities → handlers → tests.

```markdown
## Build Order

1. [ ] config.yaml (no dependencies)
2. [ ] utils.py (no dependencies)
3. [ ] main.py (depends on 1, 2)
4. [ ] test_main.py (depends on 3)
```

### Step 4: Execute Each Task

For each file, in order:

```text
┌─────────────────────────────────────────────────────┐
│                    EXECUTE TASK                      │
├─────────────────────────────────────────────────────┤
│  1. Read task from manifest                         │
│  2. Write code following DESIGN patterns            │
│     └─ Or delegate — see Delegation below           │
│  3. Run verification command                        │
│     └─ If FAIL → Fix and retry (max 3)             │
│  4. Mark task complete                              │
│  5. Move to next task                               │
└─────────────────────────────────────────────────────┘
```

Code standards for every file: no inline comments, type hints required,
self-documenting names, config in YAML over hardcoded values. Verify
incrementally — after each file, not only at the end. Fix forward: if something
breaks, fix it immediately. Keep each file independently functional.

### Step 5: Run Full Validation

After all files are created:

```bash
ruff check .        # lint
mypy .              # types (if configured)
pytest              # tests
```

Substitute the project's configured linter, type checker, and test runner when
it is not a Python project.

### Step 6: Generate the Build Report

Write `.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md`. See Output Obligations.

### Step 7: Update Statuses and Hand Off

Apply the transitions in Status Transitions, then suggest the next phase per
Handoff.

---

## Delegation

### Decision flow

```text
Has @agent-name in manifest?
├─ YES → Delegate via Task tool
│        • Provide: file path, purpose, KB domains
│        • Include: code pattern from DESIGN
│        • Agent returns: completed file
│
└─ NO (general) → Execute directly
         • Use DESIGN patterns
         • Verify against KB
         • Handle errors locally
```

### Delegation protocol

1. Extract the agent name from the manifest
2. Build the delegation prompt with context
3. Invoke via Task tool
4. Receive the completed file
5. Write to disk and verify

````markdown
Task(
  subagent_type: "{agent-name}",
  description: "Create {file_path}",
  prompt: """
    Create file: {file_path}
    Purpose: {purpose from manifest}

    Code Pattern (from DESIGN):
    ```
    {code pattern}
    ```

    KB Domains: {domains from DEFINE}

    Requirements:
    - Follow the pattern exactly
    - Use type hints (Python)
    - No inline comments
    - Return complete file content
  """
)
````

### Data engineering delegation map

When the DESIGN contains pipeline architecture, dbt models, SQL files, DAGs, or
Spark jobs, delegate by file type:

| File Type | Delegate To |
|-----------|-------------|
| `models/**/*.sql` (dbt) | `dbt-specialist` |
| `dags/**/*.py` (Airflow) | `pipeline-architect` |
| `jobs/**/*.py` (PySpark) | `spark-engineer` |
| `contracts/**/*.yaml` | `data-contracts-engineer` |
| `tests/data/**/*.py` (GE) | `data-quality-analyst` |
| `schemas/**/*.sql` | `schema-designer` |

---

## Verification

### Standard verification (per file)

```bash
ruff check {file}
mypy {file}
pytest {test_file} -v
```

If a check fails: retry up to 3 times, then treat it as a blocker (see Error
Handling).

### Data engineering verification

Detect DE artifacts in the DESIGN (dbt models, SQL files, DAGs, Spark jobs) and
run the DE-specific verification tools:

```bash
# dbt models
dbt build --select {model_name}
dbt test --select {model_name}

# SQL linting
sqlfluff lint {sql_file} --dialect {dialect}
sqlfluff fix {sql_file} --dialect {dialect}

# Great Expectations
great_expectations suite run {suite_name}

# Spark (syntax check)
python -c "from pyspark.sql import SparkSession; exec(open('{file}').read())"
```

---

## Recording Autonomous Decisions

The decide-never-ask policy itself belongs to `build-agent`; this is the
recording mechanic that makes it auditable.

Every decision fork resolved without pausing — two valid interpretations, an
ambiguous policy, a gap the DESIGN did not pre-decide — gets one row in the
BUILD_REPORT `## Autonomous Decisions` table:

| # | Decision Point | Options Considered | Chose | Rationale |
|---|----------------|--------------------|-------|-----------|

- The rationale states why the choice is the safest / smallest-correct default,
  consistent with the DESIGN and the `${CLAUDE_PLUGIN_ROOT}/kb/` patterns.
- The table is empty only if the DESIGN pre-decided everything.
- This is the post-run audit log that makes autonomous building reviewable —
  never omit a row to look decisive.

---

## Status Transitions

Contract obligation (`${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml` →
`status_transitions`): the build MUST update upstream document statuses before
completing. A stale "Ready for Build" status after a completed build is a
contract violation.

| File | Field | Value |
|------|-------|-------|
| `DEFINE_{FEATURE}.md` | Status | `✅ Complete (Built)` |
| `DESIGN_{FEATURE}.md` | Status | `✅ Complete (Built)` |
| `DEFINE_{FEATURE}.md` | Next Step | `/ship` |
| `DESIGN_{FEATURE}.md` | Next Step | `/ship` |

---

## Output Obligations

| Artifact | Location |
|----------|----------|
| Code | As specified in the DESIGN file manifest |
| Build report | `.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md` |

The report's shape is owned by `${CLAUDE_PLUGIN_ROOT}/sdd/templates/BUILD_REPORT_TEMPLATE.md`
— follow it, do not re-invent it. The sections this methodology feeds directly:
task execution with agent attribution (`@agent-name` vs `(direct)`),
verification results, and the Autonomous Decisions table.

---

## Handoff

When the build completes, suggest Phase 4:

```bash
/ship .claude/sdd/features/DEFINE_{FEATURE}.md
```

If the build stopped on blockers, recommend `/iterate` on the affected document
instead (see Error Handling).

---

## Quality Gate

Before declaring the build complete:

```text
PRE-FLIGHT CHECK
├─ [ ] All files from manifest created
├─ [ ] Each file verified (lint, types, tests)
├─ [ ] Full validation passes (lint, types, test suite)
├─ [ ] No TODO comments left in code
├─ [ ] No hardcoded secrets or credentials
├─ [ ] Error cases handled
├─ [ ] Agent attribution recorded in BUILD_REPORT
├─ [ ] Autonomous Decisions table filled (or legitimately empty)
├─ [ ] DEFINE status updated to "✅ Complete (Built)"
├─ [ ] DESIGN status updated to "✅ Complete (Built)"
└─ [ ] BUILD_REPORT generated
```

---

## Anti-Patterns

| Never Do | Why | Instead |
|----------|-----|---------|
| Skip DESIGN loading | No patterns to follow | Always load DESIGN first |
| Improvise beyond DESIGN | Scope creep; files not in manifest | Follow patterns exactly |
| Ignore agent assignments | Lose specialization | Delegate as specified |
| Skip verification | Broken code ships | Verify every file, incrementally |
| Leave TODO comments | Incomplete code | Finish or escalate |
| Explain code with inline comments | Noise; code must self-document | Self-documenting names |

---

## Error Handling

A decision fork is not an error. This table covers genuine failures — code that
will not work, not a choice between valid options.

| Error Type | Action |
|------------|--------|
| Syntax error | Fix immediately, retry |
| Import error | Check dependencies, fix |
| Simple bug | Fix immediately and continue |
| Test failure | Debug and fix |
| Decision fork (two valid options) | Not a failure — decide and record per Recording Autonomous Decisions; never stop, never ask |
| Missing requirement (DEFINE gap — DESIGN cannot be executed) | Log a blocker in BUILD_REPORT; recommend `/iterate` on DEFINE — do not pause to ask |
| Architecture problem (DESIGN pattern is wrong) | Log a blocker in BUILD_REPORT; recommend `/iterate` on DESIGN — do not pause to ask |
| Blocker (build cannot complete after retries) | Stop, document all blockers in the report, recommend `/iterate` |

CRITICAL risks (secrets, irreversible deploy, data loss) are the executor's
territory: `build-agent` owns that halt policy, and this skill never overrides
it.

---

## References

- Executor + policies: `${CLAUDE_PLUGIN_ROOT}/agents/workflow/build-agent.md`
- Entrypoint + flags: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/build.md`
- Report template: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/BUILD_REPORT_TEMPLATE.md`
- Contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml` (build block, `status_transitions`)
- Next phase: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/ship.md`
