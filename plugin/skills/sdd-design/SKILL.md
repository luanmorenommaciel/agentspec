---
name: sdd-design
description: |
  Create the architecture and technical specification for a defined feature — Phase 2 of the SDD workflow. Transforms a validated DEFINE document into a DESIGN document: architecture diagram, components, inline architecture decision records, an agent-matched file manifest, KB-grounded code patterns, and a testing strategy — then updates the DEFINE status and hands off to /build. Use when requirements are captured and technical design is needed — "design the architecture", "technical design", "Phase 2", or /design pointed at a DEFINE_*.md file. Not for capturing or clarifying requirements (that is sdd-define, Phase 1) and not for implementing code (that is sdd-build, Phase 3).
---

# SDD Design — Architecture and Technical Specification (Phase 2)

Transform a validated DEFINE document into a comprehensive DESIGN document: system architecture with diagrams, key decisions with rationale (inline ADRs), an agent-matched file manifest, KB-grounded code patterns, and a testing strategy.

This skill owns the Phase 2 methodology. The `design-agent` is the executor (identity, tools, boundaries); the `/design` command is the entrypoint (argument surface and command-only flags). Contract-grade facts — inputs, outputs, status transitions — are canonical in `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`.

## Inputs and Outputs

| Contract | Value |
|----------|-------|
| **Input** | `.claude/sdd/features/DEFINE_{FEATURE}.md` — required sections: problem statement, success criteria, acceptance tests |
| **Output** | `.claude/sdd/features/DESIGN_{FEATURE}.md` |
| **Artifact shape** | `${CLAUDE_PLUGIN_ROOT}/sdd/templates/DESIGN_TEMPLATE.md` — the authoritative section structure; follow it, do not invent sections |
| **DESIGN status values** | `Draft` → `In Progress` → `Ready for Build` (later phases advance it to `✅ Complete (Built)`, then `✅ Shipped`) |
| **On completion** | DEFINE status → `✅ Complete (Designed)` and hand off to `/build` (Step 7) |

No DEFINE, no design. If requirements are missing or incomplete, stop and route to `sdd-define` first.

## Knowledge Architecture

**KB-FIRST RESOLUTION IS MANDATORY, NOT OPTIONAL.**

```text
┌─────────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE RESOLUTION ORDER                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. KB PATTERN LOADING (from DEFINE's KB domains)                   │
│     └─ Read: ${CLAUDE_PLUGIN_ROOT}/kb/{domain}/patterns/*.md → Code patterns      │
│     └─ Read: ${CLAUDE_PLUGIN_ROOT}/kb/{domain}/concepts/*.md → Best practices     │
│     └─ Read: ${CLAUDE_PLUGIN_ROOT}/kb/{domain}/quick-reference.md → Quick lookup  │
│                                                                      │
│  2. AGENT DISCOVERY (for file manifest)                             │
│     └─ Glob: ${CLAUDE_PLUGIN_ROOT}/agents/**/*.md → Available agents              │
│     └─ Extract: Role, capabilities, keywords from each              │
│     └─ Match: Files to agents based on purpose                      │
│                                                                      │
│  3. CONFIDENCE ASSIGNMENT                                            │
│     ├─ KB patterns + agent match found    → 0.95 → Design with KB   │
│     ├─ KB patterns only                   → 0.85 → Design, note gaps│
│     ├─ Agent match only                   → 0.80 → Design, validate │
│     └─ No KB, no agent match              → 0.70 → Research first   │
│                                                                      │
│  4. MCP VALIDATION (for novel patterns)                             │
│     └─ MCP docs tool (e.g., context7, ref) → Official docs          │
│     └─ MCP search tool (e.g., exa, tavily) → Production examples    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Design Confidence Matrix

| KB Patterns | Agent Match | Confidence | Action |
|-------------|-------------|------------|--------|
| Found | Found | 0.95 | Full design with KB patterns |
| Found | Not found | 0.85 | Design with KB, general agent |
| Not found | Found | 0.80 | Design, validate patterns with MCP |
| Not found | Not found | 0.70 | Research before design |

## Process

### Step 1: Load Context

```markdown
Read(.claude/sdd/features/DEFINE_{FEATURE}.md)   # problem, users, success criteria, acceptance tests
Read(${CLAUDE_PLUGIN_ROOT}/sdd/templates/DESIGN_TEMPLATE.md)   # artifact shape
Read(CLAUDE.md)                                  # project conventions

# Explore codebase for patterns:
Glob(**/*.py) | head -20
Grep("class |def ") | sample
```

Then load KB patterns from the domains named in the DEFINE (resolution order above) and assign a confidence score from the matrix. Validate novel patterns via MCP before relying on them; at 0.70, research before designing.

### Step 2: Create Architecture

Design the solution:

| Component | Content |
|-----------|---------|
| **Overview** | ASCII diagram of the system |
| **Components** | Modules/services with purpose and technology |
| **Data Flow** | How data moves through the system |
| **Integration Points** | External dependencies |

```text
┌─────────────────────────────────────────────────────────┐
│                   SYSTEM OVERVIEW                        │
├─────────────────────────────────────────────────────────┤
│  [Input] → [Component A] → [Component B] → [Output]     │
│              ↓                 ↓                        │
│         [Storage]         [External API]                │
└─────────────────────────────────────────────────────────┘
```

### Step 3: Document Decisions (Inline ADRs)

For each significant choice:

```markdown
### Decision: {Name}

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | YYYY-MM-DD |

**Context:** Why this decision was needed

**Choice:** What we're doing

**Rationale:** Why this approach

**Alternatives Rejected:**
1. Option A - rejected because X
2. Option B - rejected because Y

**Consequences:**
- Trade-off we accept
- Benefit we gain
```

At least one decision must carry full rationale. Decisions are permanent — record the "why", not just the "what".

### Step 4: Create the File Manifest (Agent Matching)

Discover specialists, then list every file the build will create or modify:

1. Glob `${CLAUDE_PLUGIN_ROOT}/agents/**/*.md` to discover available agents
2. Extract role, capabilities, and keywords from each
3. Match files to agents:

| Match Criteria | Weight | Example |
|----------------|--------|---------|
| File type | High | `.tf` → infrastructure agent |
| Purpose keywords | High | "parsing" → domain specialist |
| Path patterns | Medium | `src/` → core developer |
| KB domain | Medium | {domain} KB → matching specialist |
| Fallback | Low | Any .py → general purpose |

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `main.py` | Create | Entry point | @{specialist-agent} | None |
| 2 | `config.yaml` | Create | Configuration | (general) | None |
| 3 | `handler.py` | Create | Request handler | @{specialist-agent} | 1, 2 |

Every file gets an agent or an explicit `(general)` fallback. Record the reasoning in the template's Agent Assignment Rationale section.

### Step 5: Define Code Patterns

1. Load patterns from the KB domains
2. Adapt to the project's existing conventions (grep the codebase)
3. Provide copy-paste ready snippets for each key pattern

```python
# Pattern: Handler structure (from ${CLAUDE_PLUGIN_ROOT}/kb/{domain}/patterns/{pattern}.md)
from config import load_config


def handler(request):
    """Entry point following KB pattern."""
    config = load_config()
    result = process(request, config)
    return {"status": "ok"}
```

### Step 6: Plan the Testing Strategy

| Test Type | Scope | Tools |
|-----------|-------|-------|
| Unit | Functions | pytest |
| Integration | API | pytest + requests |
| E2E | Full flow | Manual/automated |

The strategy must cover every acceptance test in the DEFINE.

### Step 7: Save, Update Statuses, Hand Off

1. Run the quality gate below, then write `.claude/sdd/features/DESIGN_{FEATURE_NAME}.md` following the template.
2. **Update the DEFINE document — mandatory.** Per the status transitions in `WORKFLOW_CONTRACTS.yaml`, when the design phase completes:

   | File | Field | Value |
   |------|-------|-------|
   | `DEFINE_{FEATURE}.md` | Status | `✅ Complete (Designed)` |
   | `DEFINE_{FEATURE}.md` | Next Step | `/build` |

   Skipping this leaves a stale "Ready for Design" status behind.
3. Hand off: suggest `/build .claude/sdd/features/DESIGN_{FEATURE_NAME}.md` as the next step.

## Pipeline Architecture (Data Engineering Context)

When the DEFINE contains data engineering context — sources, volumes, freshness SLAs, schema contracts — the DESIGN must also include pipeline-specific sections:

1. Detect the DE context in the DEFINE
2. Load KB patterns from the `airflow`, `streaming`, `data-modeling`, and `dbt` domains
3. Fill the template's "Pipeline Architecture (if applicable)" sections: DAG diagram, partition strategy, incremental strategy, schema evolution plan, data quality gates

The section shapes (tables and diagram formats) are defined in `DESIGN_TEMPLATE.md` — follow them, do not invent variants.

## Quality Gate

Every item must pass before the phase is declared complete:

```text
PRE-FLIGHT CHECK
├─ [ ] KB patterns loaded from DEFINE's domains
├─ [ ] ASCII architecture diagram created and clear
├─ [ ] At least one decision with full rationale (inline ADR)
├─ [ ] Complete file manifest (all files listed)
├─ [ ] Agent assigned to each file (or marked general)
├─ [ ] Code patterns are syntactically correct and copy-paste ready
├─ [ ] Testing strategy covers acceptance tests
├─ [ ] No shared dependencies across deployable units
├─ [ ] No circular dependencies in the architecture
└─ [ ] DEFINE status updated to "✅ Complete (Designed)"
```

### Contract Gate

Before handing off to `/build`, validate the document just written against this phase's contract — artifact `DESIGN_{FEATURE_NAME}.md`, phase `design`:

```bash
${CLAUDE_PLUGIN_ROOT}/tools/spec-linter/spec-lint .claude/sdd/features/DESIGN_{FEATURE_NAME}.md --phase design \
  --contracts-file ${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml
```

Run it as `${CLAUDE_PLUGIN_ROOT}/tools/spec-linter/USAGE.md` documents, and act on the verdict exactly as defined there. The exit-code contract and verdict semantics are owned by that document and by the `contract_enforcement` block (`exit_code_contract`, `verdict_semantics`) of `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml` — which is also where this phase's binding is declared. Read them there rather than assuming: a contract assigns the severity of its own rules, so never reinterpret a verdict, and never assume one the linter did not return.

## Anti-Patterns

| Never Do | Why | Instead |
|----------|-----|---------|
| Skip KB pattern loading | Inconsistent code | Always load KB first |
| Hardcode config values | Hard to change | Use YAML config files |
| Shared code across deployable units | Breaks deployments | Self-contained units |
| Circular dependencies | A depends on B depends on A | Layer the architecture, break the cycle |
| Skip agent matching | Lose specialization | Always match agents |
| Skip the testing strategy | Build has nothing to verify against | Plan tests for every requirement |
| Design without DEFINE | No requirements | Require DEFINE first |

## Design Principles

| Principle | Application |
|-----------|-------------|
| Diagram First | ASCII art clarifies thinking before prose |
| Self-Contained | Each function/service works independently |
| Config Over Code | Use YAML for tunables |
| KB Patterns | Use project KB patterns, not generic |
| Agent Specialization | Match specialists to files |
| Testable | Every component can be unit tested |
| Decisions Are Permanent | Document the "why", not just the "what" |

## Remember

> **"Design from patterns, not from scratch. Match specialists to tasks."**

**Mission:** Transform validated requirements into comprehensive technical designs with KB-grounded patterns and agent-matched file manifests.

**Core Principle:** KB first. Confidence always. Ask when uncertain.
