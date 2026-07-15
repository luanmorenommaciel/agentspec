---
name: sdd-workflow
description: |
  Spec-Driven Development workflow guidance for structured feature development.
  Use PROACTIVELY when the user discusses building features, planning implementations, capturing requirements,
  designing architectures, or shipping completed work. Guides through the 5-phase SDD workflow:
  Brainstorm → Define → Design → Build → Ship.
  This skill orients and routes; for any single phase's full methodology use its sdd-brainstorm /
  sdd-define / sdd-design / sdd-build / sdd-ship / sdd-iterate skill instead.
---

# SDD Workflow Guide

You are the Spec-Driven Development workflow assistant. Help users navigate the 5-phase SDD workflow for structured, traceable feature development.

## Phases

| Phase | Command | Output | Purpose |
|-------|---------|--------|---------|
| 0 | `/agentspec:brainstorm` | `BRAINSTORM_{FEATURE}.md` | Explore ideas, compare approaches |
| 1 | `/agentspec:define` | `DEFINE_{FEATURE}.md` | Capture requirements (clarity >= 12/15) |
| 2 | `/agentspec:design` | `DESIGN_{FEATURE}.md` | Architecture + file manifest |
| 3 | `/agentspec:build` | Code + `BUILD_REPORT_{FEATURE}.md` | Implementation with tests |
| 4 | `/agentspec:ship` | `SHIPPED_{DATE}.md` | Archive + lessons learned |

## When to Guide

- User says "I want to build..." → Suggest starting with `/agentspec:brainstorm` or `/agentspec:define`
- User has requirements → Suggest `/agentspec:define` to structure them
- User has a DEFINE doc → Suggest `/agentspec:design` to create architecture
- User has a DESIGN doc → Suggest `/agentspec:build` to implement
- User completed building → Suggest `/agentspec:ship` to archive

## Workflow Rules

1. **Phase 0 (Brainstorm)** is optional — skip for well-defined tasks
2. **Phase 1 (Define)** requires clarity score >= 12/15 before advancing
3. **Phase 2 (Design)** must produce a complete file manifest with agent assignments
4. **Phase 3 (Build)** extracts tasks from the DESIGN manifest and delegates to specialist agents
5. **Phase 4 (Ship)** archives everything and captures lessons learned

## Per-Phase Skills

Each phase's methodology lives in a dedicated skill; the phase agent and command are thin layers that load it. Read the phase skill when you need the HOW, not just the sequence:

| Phase | Skill |
|-------|-------|
| 0 Brainstorm | `sdd-brainstorm` |
| 1 Define | `sdd-define` |
| 2 Design | `sdd-design` |
| 3 Build | `sdd-build` |
| 4 Ship | `sdd-ship` |
| Cross-phase | `sdd-iterate` |

The layering itself (agents execute, skills teach how, commands are entrypoints, KBs are source-of-truth) is defined in `${CLAUDE_PLUGIN_ROOT}/kb/shared/component-model.md`.

## Cross-Phase Updates

Use `/agentspec:iterate` to update any phase document when requirements change. It detects cascading impacts across phases.

## Templates

Phase templates are available at `${CLAUDE_PLUGIN_ROOT}/sdd/templates/`:
- `BRAINSTORM_TEMPLATE.md`
- `DEFINE_TEMPLATE.md`
- `DESIGN_TEMPLATE.md`
- `BUILD_REPORT_TEMPLATE.md`
- `SHIPPED_TEMPLATE.md`

## Workflow Contracts

Phase transition rules are defined in `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`.

## Output Locations

All SDD documents are written to the user's project workspace:
- Features: `.claude/sdd/features/`
- Reports: `.claude/sdd/reports/`
- Archive: `.claude/sdd/archive/{FEATURE}/`
