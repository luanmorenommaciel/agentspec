---
name: design
description: Create architecture and technical specification (Phase 2)
---

# Design Command

> Create architecture and technical specification in one pass (Phase 2)

## Usage

```bash
/design <define-file> [--judge[=MODE]]
```

## Examples

```bash
/design .claude/sdd/features/DEFINE_NOTIFICATION_SYSTEM.md
/design DEFINE_USER_AUTH.md
/design .claude/sdd/features/DEFINE_SEARCH_API.md

# With cross-model judge for architectural soundness (opt-in)
/design DEFINE_AUTH.md --judge                  # advisory, default openai/gpt-4o
/design DEFINE_AUTH.md --judge=strict           # gated — FAIL blocks completion
/design DEFINE_AUTH.md --judge=openai/o3        # custom model (advisory)
/design DEFINE_AUTH.md --judge=strict:openai/gpt-4o  # gated + custom model
```

---

## Overview

This is **Phase 2** of the 5-phase AgentSpec workflow:

```text
Phase 0: /brainstorm → .claude/sdd/features/BRAINSTORM_{FEATURE}.md (optional)
Phase 1: /define     → .claude/sdd/features/DEFINE_{FEATURE}.md
Phase 2: /design     → .claude/sdd/features/DESIGN_{FEATURE}.md (THIS COMMAND)
Phase 3: /build      → Code + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
Phase 4: /ship       → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md
```

The `/design` command combines what used to be Plan + Spec + ADRs into a single document with architecture decisions inline.

---

## What Happens

1. **Load the skill** — read `.claude/skills/sdd-design/SKILL.md`. It owns the Phase 2 methodology: KB-first resolution, the architecture and inline-ADR steps, the agent-matched file manifest, code patterns, the testing strategy, and the quality gate.
2. **Follow it end to end** (Steps 1–7) for the given `<define-file>`.
3. **Produce the DESIGN document** at `.claude/sdd/features/DESIGN_{FEATURE_NAME}.md`, update the DEFINE status per `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`, and suggest `/build` as the next step.

The judge pass below is command-only — it runs after the skill's Step 7, and only when `--judge` is passed.

### Step 8: Optional Judge Pass (`--judge`)

Runs only if the user invoked with `--judge[=MODE]`. Cross-model second
opinion on the design, focused on architectural soundness — hallucinated
APIs, wrong invariants, unsafe defaults, missing edge cases, unjustified
decisions.

**Flag parsing (parse from the user's command args):**

| Input | Mode | Model |
|-------|------|-------|
| `--judge` | advisory | phase default (openai/gpt-4o for design) |
| `--judge=strict` | gated | phase default |
| `--judge=MODEL_SLUG` | advisory | MODEL_SLUG |
| `--judge=strict:MODEL_SLUG` | gated | MODEL_SLUG |

**Execution (after the DESIGN file is written):**

```bash
MODEL=""   # empty → judge.py picks phase default
STRICT_FLAG=""
[[ "$mode" == "strict" ]] && STRICT_FLAG="--strict"

python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/judge.py \
  ".claude/sdd/features/DESIGN_{FEATURE_NAME}.md" \
  --phase design \
  ${MODEL:+--model "$MODEL"} \
  ${STRICT_FLAG} \
  --context "DESIGN document (Phase 2) — check architectural soundness, edge cases, API correctness, and unsafe defaults. FEATURE: {FEATURE_NAME}"
```

**Interpreting the verdict:**

- **Advisory mode (`--judge` or `--judge=MODEL`):**
  - Show the judge's markdown verdict to the user below the normal phase summary
  - If FAIL: surface concerns + suggested fixes; phase is still marked complete
  - User decides whether to iterate before `/build`
- **Gated mode (`--judge=strict` or `--judge=strict:MODEL`):**
  - If PASS: phase is complete, proceed to suggest `/build`
  - If FAIL: phase is NOT marked complete. Surface concerns + suggested fixes.
    Tell the user: "DESIGN did not pass the judge. Address the concerns and
    re-run /design, or override with --judge=strict --force to treat FAIL as
    advisory."

**Budget / error handling:**

- Exit 3 (budget exhausted): surface ledger, continue as if `--judge` was not passed
- Exit 2 (config error): surface setup pointer to `docs/getting-started/judge-setup.md`, continue
- Exit 4 (network/API error): surface, continue advisory

---

## References

- Skill: `.claude/skills/sdd-design/SKILL.md`
- Agent: `.claude/agents/workflow/design-agent.md`
- Template: `.claude/sdd/templates/DESIGN_TEMPLATE.md`
- Contracts: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Next Phase: `.claude/commands/workflow/build.md`
