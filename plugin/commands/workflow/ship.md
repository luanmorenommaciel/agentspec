---
name: ship
description: Archive completed feature with lessons learned (Phase 4)
---

# Ship Command

> Archive completed feature with lessons learned (Phase 4)

## Usage

```bash
/ship <define-file>
```

## Examples

```bash
/ship .claude/sdd/features/DEFINE_NOTIFICATION_SYSTEM.md
/ship DEFINE_USER_AUTH.md
```

---

## Overview

This is **Phase 4** — the close of the 5-phase AgentSpec workflow:

```text
Phase 0: /brainstorm → .claude/sdd/features/BRAINSTORM_{FEATURE}.md (optional)
Phase 1: /define     → .claude/sdd/features/DEFINE_{FEATURE}.md
Phase 2: /design     → .claude/sdd/features/DESIGN_{FEATURE}.md
Phase 3: /build      → Code + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
Phase 4: /ship       → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md (THIS COMMAND)
```

---

## What Happens

1. **Load the skill** — read `${CLAUDE_PLUGIN_ROOT}/skills/sdd-ship/SKILL.md`; it owns the full ship methodology.
2. **Verify completeness** — all artifacts present, BUILD_REPORT complete, all tests passing. An incomplete build is refused and routed back to `/build`.
3. **Archive** — copy every phase artifact to `.claude/sdd/archive/{FEATURE}/` and update all document statuses to "Shipped".
4. **Extract lessons** — capture specific, actionable lessons learned in the SHIPPED document (per `SHIPPED_TEMPLATE.md`).
5. **Close the cycle** — clean the working files from `features/` and `reports/`, then hand off. Start the next feature with `/define`.

---

## References

- Skill: `${CLAUDE_PLUGIN_ROOT}/skills/sdd-ship/SKILL.md`
- Agent: `${CLAUDE_PLUGIN_ROOT}/agents/workflow/ship-agent.md`
- Template: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/SHIPPED_TEMPLATE.md`
- Contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Previous Phase: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/build.md`
