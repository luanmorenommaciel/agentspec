---
name: brainstorm
description: Explore ideas through collaborative dialogue before requirements capture (Phase 0)
---

# Brainstorm Command

> Phase 0 of the SDD workflow — optional, and the only phase that starts from nothing but an idea. Its output feeds `/define` (Phase 1).

## Usage

```bash
/brainstorm <idea-or-request>
/brainstorm "Build a real-time notification system"
/brainstorm notes/rough-idea.txt
```

**Arguments:** a quoted idea, problem statement, or feature request — or a path to a file containing rough notes.

## Examples

```bash
# From a direct idea
/brainstorm "I want to automate data quality checks"

# From a file with notes
/brainstorm docs/meeting-notes.md

# From a problem statement
/brainstorm "Our team spends too much time on manual data entry"
```

## What happens

1. Load `.claude/skills/sdd-brainstorm/SKILL.md` and follow it — the skill owns the methodology: KB-first grounding, one-question-at-a-time discovery, sample collection, 2-3 approach comparison, YAGNI, incremental validation, and the quality gate.
2. Produce the BRAINSTORM artifact at `.claude/sdd/features/BRAINSTORM_{FEATURE}.md`, shaped by `.claude/sdd/templates/BRAINSTORM_TEMPLATE.md`.
3. Suggest the next step: `/define .claude/sdd/features/BRAINSTORM_{FEATURE}.md`.

## When to use /brainstorm vs /define

| Scenario | Use |
|----------|-----|
| Vague idea, need to explore | `/brainstorm` |
| Clear requirements, ready to capture | `/define` directly |
| Existing BRAINSTORM document | `/define <brainstorm-file>` |
| Meeting notes with clear asks | `/define` directly |
| "I want to build something but not sure what" | `/brainstorm` |

## References

- Skill (methodology): `.claude/skills/sdd-brainstorm/SKILL.md`
- Agent (executor): `.claude/agents/workflow/brainstorm-agent.md`
- Template (artifact shape): `.claude/sdd/templates/BRAINSTORM_TEMPLATE.md`
- Contracts (phase obligations): `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Next phase: `.claude/commands/workflow/define.md`
