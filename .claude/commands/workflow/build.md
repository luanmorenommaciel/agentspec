# Build Command

> Execute implementation with on-the-fly task generation (Phase 3)

## Usage

```bash
/build <design-file>
```

## Examples

```bash
/build .claude/sdd/features/DESIGN_CLOUD_RUN_FUNCTIONS.md
/build DESIGN_USER_AUTH.md
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
Read(.claude/CLAUDE.md)
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
