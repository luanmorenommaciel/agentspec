---
name: build
description: Execute implementation with on-the-fly task generation (Phase 3)
---

# Build Command

> Execute implementation with on-the-fly task generation (Phase 3)

## Usage

```bash
/build <design-file> [--judge[=MODE]]
```

## Examples

```bash
/build .claude/sdd/features/DESIGN_NOTIFICATION_SYSTEM.md
/build DESIGN_USER_AUTH.md

# With cross-model judge for code correctness (opt-in, advisory for build)
/build DESIGN_AUTH.md --judge                 # advisory, default openai/gpt-4o
/build DESIGN_AUTH.md --judge=openai/codex-mini    # code-tuned model (cheaper)
/build DESIGN_AUTH.md --judge=strict          # gated on BUILD_REPORT quality
```

---

## Overview

This is **Phase 3** of the 5-phase AgentSpec workflow:

```text
Phase 0: /brainstorm → .claude/sdd/features/BRAINSTORM_{FEATURE}.md (optional)
Phase 1: /define     → .claude/sdd/features/DEFINE_{FEATURE}.md
Phase 2: /design   → .claude/sdd/features/DESIGN_{FEATURE}.md
Phase 3: /build    → Code + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md (THIS COMMAND)
Phase 4: /ship     → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md
```

The `/build` command executes the implementation, generating tasks on-the-fly from the file manifest.

---

## What This Command Does

1. **Parse** - Extract file manifest from DESIGN
2. **Prioritize** - Order files by dependencies
3. **Execute** - Create each file with verification
4. **Validate** - Run tests after each significant change
5. **Report** - Generate build report

---

## Process

### Step 1: Load Context

```markdown
Read(.claude/sdd/features/DESIGN_{FEATURE}.md)
Read(.claude/sdd/features/DEFINE_{FEATURE}.md)
Read(CLAUDE.md)
```

### Step 2: Extract Tasks from File Manifest

Convert the file manifest to a task list:

```markdown
From DESIGN file manifest:
| File | Action | Purpose |

Generate:
- [ ] Create/Modify {file1}
- [ ] Create/Modify {file2}
- [ ] ...
```

### Step 3: Order by Dependencies

Analyze imports and dependencies to determine execution order.

### Step 4: Execute Each Task

For each file:

1. **Write** - Create the file following code patterns from DESIGN
2. **Verify** - Run verification command (lint, type check, import test)
3. **Mark Complete** - Update progress

### Step 5: Run Full Validation

After all files created:

```bash
# Lint check
ruff check .

# Type check (if applicable)
mypy .

# Run tests
pytest
```

### Step 6: Generate Build Report

```markdown
Write(.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md)
```

### Step 7: Optional Judge Pass (`--judge`)

Runs only if the user invoked with `--judge[=MODE]`. Cross-model second
opinion on the BUILD_REPORT (which references the actual code written),
focused on concrete bugs — logic errors, concurrency, security, SQL
correctness, IAM/RLS, data loss risks.

**Flag parsing (parse from the user's command args):**

| Input | Mode | Model |
|-------|------|-------|
| `--judge` | advisory | phase default (openai/gpt-4o for build) |
| `--judge=strict` | gated | phase default |
| `--judge=MODEL_SLUG` | advisory | MODEL_SLUG |
| `--judge=strict:MODEL_SLUG` | gated | MODEL_SLUG |

**Note on model choice for /build:** `openai/codex-mini` is a strong,
cheaper choice for pure-code review. Use `openai/gpt-4o` (the default)
when the build touches architecture or spans multiple files.

**Execution (after BUILD_REPORT is written):**

```bash
MODEL=""   # empty → judge.py picks phase default
STRICT_FLAG=""
[[ "$mode" == "strict" ]] && STRICT_FLAG="--strict"

python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/judge.py \
  ".claude/sdd/reports/BUILD_REPORT_{FEATURE}.md" \
  --phase build \
  ${MODEL:+--model "$MODEL"} \
  ${STRICT_FLAG} \
  --context "BUILD_REPORT (Phase 3) — check concrete code correctness, security, SQL / IAM / RLS issues, data loss risks. FEATURE: {FEATURE}"
```

**Alternative per-file judging (for large builds):**

For builds that produce many files, consider judging the most critical
files individually instead of the whole report:

```bash
# Judge the single riskiest file (migration, IAM, critical SQL)
python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/judge.py \
  "migrations/2026_X_add_roles.sql" \
  --phase build \
  --context "Postgres migration adding NOT NULL column on 50M-row table"
```

**Interpreting the verdict:**

- **Advisory mode:** Show judge verdict, phase still complete, user decides
- **Gated mode:** PASS → complete + suggest `/ship`. FAIL → phase not complete,
  surface concerns, user iterates or forces with `--force`

**Budget / error handling:**

- Exit 3 (budget): surface ledger, continue as if `--judge` was not passed
- Exit 2 (config): surface setup pointer, continue
- Exit 4 (network): surface, continue advisory

---

## Output

| Artifact | Location |
|----------|----------|
| **Code** | As specified in DESIGN file manifest |
| **Build Report** | `.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md` |

**Next Step:** `/ship .claude/sdd/features/DEFINE_{FEATURE}.md` (when ready)

---

## Execution Loop

The build agent follows this loop for each task:

```text
┌─────────────────────────────────────────────────────┐
│                    EXECUTE TASK                      │
├─────────────────────────────────────────────────────┤
│  1. Read task from manifest                         │
│  2. Write code following DESIGN patterns            │
│  3. Run verification command                        │
│     └─ If FAIL → Fix and retry (max 3)             │
│  4. Mark task complete                              │
│  5. Move to next task                               │
└─────────────────────────────────────────────────────┘
```

---

## Quality Gate

Before marking complete, verify:

```text
[ ] All files from manifest created
[ ] All verification commands pass
[ ] Lint check passes
[ ] Tests pass (if applicable)
[ ] No TODO comments left in code
[ ] Build report generated
```

---

## Tips

1. **Follow the DESIGN** - Don't improvise, use the code patterns
2. **Verify Incrementally** - Test after each file, not at the end
3. **Fix Forward** - If something breaks, fix it immediately
4. **Self-Contained** - Each file should be independently functional
5. **No Comments** - Code should be self-documenting

---

## Handling Issues During Build

If you encounter issues:

| Issue | Action |
|-------|--------|
| Missing requirement | Use `/iterate` to update DEFINE |
| Architecture problem | Use `/iterate` to update DESIGN |
| Simple bug | Fix immediately and continue |
| Major blocker | Stop and report in build report |

---

## References

- Agent: `.claude/agents/workflow/build-agent.md`
- Template: `.claude/sdd/templates/BUILD_REPORT_TEMPLATE.md`
- Contracts: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Next Phase: `.claude/commands/workflow/ship.md`
