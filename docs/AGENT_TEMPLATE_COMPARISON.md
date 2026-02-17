# Agent Template Comparison: Before vs After

This document demonstrates the improvements made to the AgentSpec agent template, making **KB-First architecture** and **Confidence Scoring** first-class citizens.

## Executive Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Template Lines | 387 | ~160 | **59% reduction** |
| KB-First Location | Line 148 (buried) | Line 32 (Section 2) | **First-class citizen** |
| Confidence Scoring | Optional appendix | Core architecture | **Mandatory pattern** |
| Grounding Loops | Common | Prevented | **Token savings** |
| Agent Consistency | Varied | Standardized | **Uniform quality** |

---

## Key Structural Changes

### Before: KB as Afterthought

```text
OLD TEMPLATE STRUCTURE (387 lines)
├── Frontmatter (1-27)
├── Quick Reference (29-50)
├── Validation System (52-82)           ← Generic "validation"
│   └── Agreement Matrix
│   └── Confidence Modifiers
│   └── Task Thresholds
├── Execution Template (84-120)         ← Verbose execution form
├── Context Loading (122-145)
├── Capabilities (147-200)
│   └── "KB CHECK" buried here (line 148) ← KB hidden in capabilities!
├── Response Formats (202-280)
├── Error Recovery (282-320)
├── Anti-Patterns (322-360)
├── Quality Checklist (362-380)
└── Remember (382-387)
```

### After: KB as First-Class Citizen

```text
NEW TEMPLATE STRUCTURE (~160 lines)
├── Frontmatter (1-22)
│   └── kb_domains: [{domain}]          ← KB domains in frontmatter
├── Identity Block (24-29)
│   └── Threshold stated upfront
├── Knowledge Architecture (31-58)      ← KB-FIRST IS SECTION 2!
│   └── "THIS AGENT FOLLOWS KB-FIRST RESOLUTION"
│   └── Resolution Order Box
│   └── Confidence Matrix
├── Capabilities (60-106)
├── Quality Gate (108-130)
├── Response Format (132-150)
└── Remember (152-160)
```

---

## Before/After: Real Example

### BEFORE: code-reviewer.md (excerpt)

```markdown
## Validation System

### Agreement Matrix

                    │ MCP AGREES     │ MCP DISAGREES  │ MCP SILENT     │
────────────────────┼────────────────┼────────────────┼────────────────┤
KB HAS PATTERN      │ HIGH: 0.95     │ CONFLICT: 0.50 │ MEDIUM: 0.75   │
                    │ → Execute      │ → Investigate  │ → Proceed      │
────────────────────┼────────────────┼────────────────┼────────────────┤
KB SILENT           │ MCP-ONLY: 0.85 │ N/A            │ LOW: 0.50      │
                    │ → Proceed      │                │ → Ask User     │

### Capabilities

### Capability 1: Code Review

**When:** After code is written

**Process:**
1. Check KB for patterns                    ← KB mentioned casually
2. If found: Apply pattern
3. If uncertain: Query MCP
...
```

**Problems:**
- KB check is just one step in a capability
- No enforcement of KB-first
- Confidence scoring disconnected from workflow

### AFTER: code-reviewer.md (excerpt)

```markdown
## Knowledge Architecture

**THIS AGENT FOLLOWS KB-FIRST RESOLUTION. This is mandatory, not optional.**

┌─────────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE RESOLUTION ORDER                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. KB CHECK (project-specific patterns)                            │
│     └─ Read: .claude/kb/{domain}/patterns/*.md → Code patterns      │
│     └─ Read: .claude/CLAUDE.md → Project conventions                │
│     └─ Grep: Existing codebase patterns                             │
│                                                                      │
│  2. CONFIDENCE ASSIGNMENT                                            │
│     ├─ KB pattern match + OWASP match   → 0.95 → Flag issue         │
│     ├─ KB pattern match only            → 0.85 → Flag with context  │
│     ├─ Pattern uncertain                → 0.70 → Suggest, ask intent│
│     └─ Domain-specific code             → 0.60 → Note, don't block  │
│                                                                      │
│  3. MCP VALIDATION (for security concerns)                          │
│     └─ mcp__upstash-context-7-mcp__query-docs → Best practices      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Improvements:**
- KB-First is **mandatory and prominent**
- Resolution order is **visual and clear**
- Confidence is **calculated based on evidence**
- MCP is explicitly a **fallback, not first choice**

---

## Value Proposition

### 1. Token Efficiency

```text
BEFORE (Grounding Loop):
User: "Review this code"
Agent: Query MCP for best practices      ← External call
Agent: Query MCP for security patterns   ← External call
Agent: Query MCP for code style          ← External call
Agent: Now review code...
Total: 3 MCP calls, ~15,000 tokens

AFTER (KB-First):
User: "Review this code"
Agent: Read .claude/kb/security/         ← Local, instant
Agent: Confidence 0.90, execute review
Total: 0 MCP calls, ~500 tokens

SAVINGS: ~97% token reduction on repeated tasks
```

### 2. Velocity Improvement

| Scenario | Before | After |
|----------|--------|-------|
| First review in domain | MCP research | MCP research (same) |
| Second review in domain | MCP research again | KB lookup (instant) |
| 10th review in domain | MCP research again | KB lookup (instant) |

**KB acts as a grounding cache** - query once, use forever.

### 3. Consistency

```text
BEFORE: Each agent had different structure
- Some had KB sections
- Some didn't mention KB at all
- Confidence was optional

AFTER: All agents follow same pattern
- KB-First is Section 2 in every agent
- Confidence is always calculated
- Response always includes confidence score
```

---

## Core Agent Inventory

All 15 core agents now follow the KB-First template:

### Workflow (6)
- ✅ brainstorm-agent
- ✅ define-agent
- ✅ design-agent
- ✅ build-agent
- ✅ ship-agent
- ✅ iterate-agent

### Code Quality (4)
- ✅ code-reviewer
- ✅ code-cleaner
- ✅ code-documenter
- ✅ test-generator

### Communication (3)
- ✅ adaptive-explainer
- ✅ meeting-analyst
- ✅ the-planner

### Exploration (2)
- ✅ codebase-explorer
- ✅ kb-architect

---

## Migration Guide

To update an existing agent to the new template:

1. **Add `kb_domains` to frontmatter**
   ```yaml
   kb_domains: [your-domain]
   ```

2. **Add Knowledge Architecture section after Identity**
   ```markdown
   ## Knowledge Architecture

   **THIS AGENT FOLLOWS KB-FIRST RESOLUTION.**

   [Resolution order box with KB → Confidence → MCP]
   ```

3. **Add Confidence Matrix**
   - Define what evidence gives what confidence
   - Define threshold for this agent type

4. **Update Response Format**
   - Always include: `**Confidence:** {score} | **Source:** {KB or MCP}`

5. **Add to Quality Gate**
   - `[ ] KB checked first`
   - `[ ] Confidence calculated`
   - `[ ] Sources cited`

---

## Conclusion

The new KB-First template transforms agents from:

> "Maybe check KB, probably query MCP, hope for the best"

To:

> "Always check KB first, calculate confidence, only query MCP when needed"

This results in:
- **Faster responses** (local KB vs external MCP)
- **Lower token usage** (grounding cache)
- **Consistent quality** (standardized template)
- **Predictable behavior** (confidence thresholds)

---

*Generated during AgentSpec restructuring - 2026-02-03*
