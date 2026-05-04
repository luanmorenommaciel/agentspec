---
name: define
description: Capture and validate requirements in one pass (Phase 1)
---

# Define Command

> Capture requirements and validate them in one pass (Phase 1)

## Usage

```bash
/define <input> [--judge[=MODE]]
```

## Examples

```bash
# From a BRAINSTORM document (recommended after /brainstorm)
/define .claude/sdd/features/BRAINSTORM_NOTIFICATION_SYSTEM.md

# From meeting notes or raw input
/define notes/meeting-notes.md
/define "Build an API gateway for user management"
/define docs/stakeholder-email.txt

# With cross-model judge for spec quality verification (opt-in)
/define BRAINSTORM_AUTH.md --judge                  # advisory, default openai/gpt-4o
/define BRAINSTORM_AUTH.md --judge=strict           # gated — FAIL blocks completion
/define BRAINSTORM_AUTH.md --judge=anthropic/claude-opus-4  # custom model (advisory)
/define BRAINSTORM_AUTH.md --judge=strict:openai/gpt-4o     # gated + custom model
```

---

## Overview

This is **Phase 1** of the 5-phase AgentSpec workflow:

```text
Phase 0: /brainstorm → .claude/sdd/features/BRAINSTORM_{FEATURE}.md (optional)
Phase 1: /define     → .claude/sdd/features/DEFINE_{FEATURE}.md (THIS COMMAND)
Phase 2: /design     → .claude/sdd/features/DESIGN_{FEATURE}.md
Phase 3: /build      → Code + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
Phase 4: /ship       → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md
```

The `/define` command combines what used to be Intake + PRD + Refine into a single, iterative phase. When fed a BRAINSTORM document, it extracts pre-validated requirements with minimal clarification needed.

---

## What This Command Does

1. **Extract** - Pull requirements from any input (notes, emails, conversations)
2. **Structure** - Organize into problem, users, goals, success criteria
3. **Validate** - Built-in clarity scoring (must reach 12/15 to proceed)
4. **Clarify** - Ask targeted questions for any gaps

---

## Process

### Step 1: Load Context

```markdown
Read(${CLAUDE_PLUGIN_ROOT}/sdd/templates/DEFINE_TEMPLATE.md)
Read(CLAUDE.md)

# If file provided:
Read(<input-file>)
```

### Step 2: Classify Input

Identify the input type to guide extraction:

| Input Type | Pattern | Focus |
|------------|---------|-------|
| `brainstorm_document` | BRAINSTORM_*.md from /brainstorm | Pre-validated, extract directly |
| `meeting_notes` | Bullet points, action items | Decisions, requirements |
| `email_thread` | Re:, Fwd:, signatures | Requests, constraints |
| `conversation` | Informal language | Core problem, users |
| `direct_requirement` | Structured request | All elements present |
| `mixed_sources` | Multiple formats | Consolidate, deduplicate |

**Note:** When input is a BRAINSTORM document, extraction is streamlined because:
- Discovery questions are already answered
- Approaches have been evaluated
- YAGNI has been applied
- User has validated the direction

### Step 3: Extract Entities

Extract these elements from input:

| Element | Extraction Patterns |
|---------|---------------------|
| **Problem** | "We're struggling with...", "The issue is...", "Pain point:" |
| **Users** | "For the team...", "Customers want...", "Users need..." |
| **Goals** | "We need to...", "Goal is to...", "Success looks like..." |
| **Success Criteria** | "Success means...", "We'll know when...", "Measured by..." |
| **Acceptance Tests** | "Given/When/Then", "Test case:", "Scenario:" |
| **Constraints** | "Must work with...", "Can't change...", "Limited by..." |
| **Out of Scope** | "Not including...", "Deferred to...", "Excluded:" |

### Step 4: Calculate Clarity Score

Score each element (0-3 points):

| Element | Score | Meaning |
|---------|-------|---------|
| Problem | 0-3 | Clear, specific, actionable |
| Users | 0-3 | Identified with pain points |
| Goals | 0-3 | Measurable outcomes |
| Success | 0-3 | Testable criteria |
| Scope | 0-3 | Explicit boundaries |

**Scoring Guide:**
- 0 = Missing entirely
- 1 = Vague or incomplete
- 2 = Clear but missing details
- 3 = Crystal clear, actionable

**Minimum to proceed:** 12/15 (80%)

### Step 5: Fill Gaps (if needed)

If score < 12, use `AskUserQuestion` with specific options:

```markdown
Example questions:
- "Who is the primary user: (a) internal team, (b) customers, (c) both?"
- "What's the timeline: (a) this sprint, (b) this quarter, (c) no deadline?"
```

### Step 6: Generate Document

Write the structured document following the template, then save:

```markdown
Write(.claude/sdd/features/DEFINE_{FEATURE_NAME}.md)
```

### Step 7: Optional Judge Pass (`--judge`)

Runs only if the user invoked with `--judge[=MODE]`. This is a cross-model
second opinion on the spec you just wrote, using a non-Claude model via
OpenRouter. Defaults are designed so most users never notice the flag exists.

**Flag parsing (parse from the user's command args):**

| Input | Mode | Model |
|-------|------|-------|
| `--judge` | advisory | phase default (openai/gpt-4o for define) |
| `--judge=strict` | gated | phase default |
| `--judge=MODEL_SLUG` | advisory | MODEL_SLUG |
| `--judge=strict:MODEL_SLUG` | gated | MODEL_SLUG |

**Execution (after the DEFINE file is written):**

```bash
# Resolve model and mode from the flag
MODEL=""   # empty → judge.py picks phase default
STRICT_FLAG=""
[[ "$mode" == "strict" ]] && STRICT_FLAG="--strict"

python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/judge.py \
  ".claude/sdd/features/DEFINE_{FEATURE_NAME}.md" \
  --phase define \
  ${MODEL:+--model "$MODEL"} \
  ${STRICT_FLAG} \
  --context "DEFINE document (Phase 1) — check requirements quality, acceptance criteria, testability, and contradictions. FEATURE: {FEATURE_NAME}"
```

**Interpreting the verdict:**

- **Advisory mode (`--judge` or `--judge=MODEL`):**
  - Show the judge's markdown verdict to the user below the normal phase summary
  - If FAIL: surface the concerns + suggested fixes; phase is still marked complete
  - User decides whether to iterate (re-run `/define` with clarifications) before `/design`
- **Gated mode (`--judge=strict` or `--judge=strict:MODEL`):**
  - If PASS: phase is complete, proceed to suggest `/design`
  - If FAIL: phase is NOT marked complete. Surface concerns + suggested fixes.
    Tell the user: "DEFINE did not pass the judge. Address the concerns and
    re-run /define, or override with /define {input} --judge=strict --force
    (treat FAIL as advisory)"

**Budget awareness:**

If `judge.py` exits with code 3 (daily budget exhausted), surface the ledger
status and continue as if `--judge` was not passed. Never block the phase on
budget exhaustion.

**Error handling:**

- Exit code 2 (config error, e.g., missing `OPENROUTER_API_KEY`): show the
  error to the user with setup pointer to `docs/getting-started/judge-setup.md`
  and continue as if `--judge` was not passed
- Exit code 4 (network / API error): surface the error, continue advisory

---

## Output

| Artifact | Location |
|----------|----------|
| **DEFINE** | `.claude/sdd/features/DEFINE_{FEATURE_NAME}.md` |

**Next Step:** `/design .claude/sdd/features/DEFINE_{FEATURE_NAME}.md`

---

## Quality Gate

Before saving, verify:

```text
[ ] Problem statement is clear and specific
[ ] At least one user persona identified
[ ] Success criteria are measurable
[ ] Acceptance tests are testable
[ ] Out of scope is explicit
[ ] Clarity Score >= 12/15
```

---

## Tips

1. **Be Specific** - "Improve performance" → "Reduce API latency to <200ms"
2. **Use Numbers** - "Handle many users" → "Support 1000 concurrent users"
3. **Test Criteria** - If you can't test it, it's not clear enough
4. **Scope Ruthlessly** - What's OUT is as important as what's IN

---

## References

- Agent: `${CLAUDE_PLUGIN_ROOT}/agents/workflow/define-agent.md`
- Template: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/DEFINE_TEMPLATE.md`
- Contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Previous Phase: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/brainstorm.md` (optional)
- Next Phase: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/design.md`
