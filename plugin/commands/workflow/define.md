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

## What happens

This command is the Phase 1 entrypoint; the methodology — process steps, scoring rubric, quality gate, anti-patterns — lives in the skill, not here.

1. Load `${CLAUDE_PLUGIN_ROOT}/skills/sdd-define/SKILL.md` and follow it: input classification, entity extraction, technical and data engineering context, clarity scoring against the 12/15 gate, gap filling.
2. Produce the DEFINE document at `.claude/sdd/features/DEFINE_{FEATURE_NAME}.md` (structure: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/DEFINE_TEMPLATE.md`) and update document statuses per the workflow contracts.
3. Suggest the next phase: `/design .claude/sdd/features/DEFINE_{FEATURE_NAME}.md`.

---

## Optional Judge Pass (`--judge`)

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

## References

- Skill (methodology): `${CLAUDE_PLUGIN_ROOT}/skills/sdd-define/SKILL.md`
- Agent (executor): `${CLAUDE_PLUGIN_ROOT}/agents/workflow/define-agent.md`
- Template: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/DEFINE_TEMPLATE.md`
- Contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Previous Phase: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/brainstorm.md` (optional)
- Next Phase: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/design.md`
