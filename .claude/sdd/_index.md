# AgentSpec 4.2

> 5-phase development workflow with Agent Matching and Delegation.
> *"Brainstorm → Define → Design → Build → Ship"*

---

## Overview

AgentSpec 4.2 adds Agent Matching (Design phase) and Agent Delegation (Build phase):

| Before (v3.x) | After (v4.1) |
|---------------|--------------|
| 8 phases | **5 phases** (Brainstorm optional) |
| 3 development modes | **1 unified stream** |
| 12+ commands | **6 commands** |
| 11+ artifact types | **5 artifact types** |
| Separate ADR files | **Inline decisions** |
| Pre-generated tasks | **On-the-fly execution** |
| Jump to requirements | **Explore first (optional)** |

---

## The 5-Phase Pipeline

```text
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Phase 0    │───▶│   Phase 1    │───▶│   Phase 2    │───▶│   Phase 3    │───▶│   Phase 4    │
│  BRAINSTORM  │    │   DEFINE     │    │   DESIGN     │    │    BUILD     │    │    SHIP      │
│  (Explore)   │    │  (What+Why)  │    │    (How)     │    │     (Do)     │    │   (Close)    │
│  [Optional]  │    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
└──────────────┘           │                   │                   │                   │
       │                   ▼                   ▼                   ▼                   ▼
       ▼              DEFINE_*.md         DESIGN_*.md        Code + Report       SHIPPED_*.md
  BRAINSTORM_*.md

       ◀─────────────────────────────────────────────────────────────────────────────────▶
                                    /iterate (any phase)
```

---

## Commands

| Command | Phase | Purpose | Model |
|---------|-------|---------|-------|
| `/brainstorm` | 0 | Explore ideas through collaborative dialogue | Opus |
| `/define` | 1 | Capture and validate requirements | Opus |
| `/design` | 2 | Create architecture and specification | Opus |
| `/build` | 3 | Execute implementation with verification | Sonnet |
| `/ship` | 4 | Archive with lessons learned | Haiku |
| `/iterate` | Any | Update documents when changes needed | Sonnet |

---

## Artifacts

| Artifact | Phase | Location |
|----------|-------|----------|
| `BRAINSTORM_{FEATURE}.md` | 0 | `.claude/sdd/features/` |
| `DEFINE_{FEATURE}.md` | 1 | `.claude/sdd/features/` |
| `DESIGN_{FEATURE}.md` | 2 | `.claude/sdd/features/` |
| `BUILD_REPORT_{FEATURE}.md` | 3 | `.claude/sdd/reports/` |
| `SHIPPED_{DATE}.md` | 4 | `.claude/sdd/archive/{FEATURE}/` |

---

## Quick Start

### Starting a New Feature (with Brainstorm)

```bash
# Phase 0: Explore the idea (optional but recommended for vague ideas)
/brainstorm "I want to build a user notification system"

# Phase 1: Define requirements (from brainstorm output)
/define .claude/sdd/features/BRAINSTORM_USER_NOTIFICATIONS.md

# Phase 2: Create technical design
/design .claude/sdd/features/DEFINE_USER_NOTIFICATIONS.md

# Phase 3: Build the code
/build .claude/sdd/features/DESIGN_USER_NOTIFICATIONS.md

# Phase 4: Archive when complete
/ship .claude/sdd/features/DEFINE_USER_NOTIFICATIONS.md
```

### Starting with Clear Requirements (skip Brainstorm)

```bash
# Phase 1: Define requirements directly
/define "Build a REST API for user management"

# Continue with /design → /build → /ship
```

### Making Changes Mid-Stream

```bash
# Update BRAINSTORM with new approach
/iterate BRAINSTORM_USER_AUTH.md "Consider using OAuth instead of custom tokens"

# Update DEFINE with new requirement
/iterate DEFINE_DATA_EXPORT.md "Add support for CSV format"

# Update DESIGN with architecture change
/iterate DESIGN_DATA_EXPORT.md "Components need to be self-contained"
```

---

## Folder Structure

```text
.claude/sdd/
├── _index.md                    # This file
├── README.md                    # Comprehensive documentation
├── features/                    # Active feature documents
│   ├── BRAINSTORM_{FEATURE}.md
│   ├── DEFINE_{FEATURE}.md
│   └── DESIGN_{FEATURE}.md
├── reports/                     # Build reports
│   └── BUILD_REPORT_{FEATURE}.md
├── archive/                     # Shipped features
│   └── {FEATURE}/
│       ├── BRAINSTORM_{FEATURE}.md  (if used)
│       ├── DEFINE_{FEATURE}.md
│       ├── DESIGN_{FEATURE}.md
│       ├── BUILD_REPORT_{FEATURE}.md
│       └── SHIPPED_{DATE}.md
├── examples/                    # Real-world examples
│   ├── README.md
│   ├── BRAINSTORM_*.md
│   ├── DEFINE_*.md
│   ├── DESIGN_*.md
│   └── BUILD_REPORT_*.md
├── templates/                   # Document templates
│   ├── BRAINSTORM_TEMPLATE.md
│   ├── DEFINE_TEMPLATE.md
│   ├── DESIGN_TEMPLATE.md
│   ├── BUILD_REPORT_TEMPLATE.md
│   └── SHIPPED_TEMPLATE.md
└── architecture/                # Workflow contracts
    ├── WORKFLOW_CONTRACTS.yaml
    └── ARCHITECTURE.md
```

---

## Phase Details

### Phase 0: Brainstorm (Optional)

**Purpose:** Explore ideas through collaborative dialogue before capturing requirements.

**When to Use:**
- Vague idea that needs exploration
- Multiple possible approaches to consider
- Uncertain about scope or users
- Need to apply YAGNI before diving in

**When to Skip:**
- Clear requirements already known
- Meeting notes with explicit asks
- Simple feature request

**Input:** Raw idea, problem statement, or vague request.

**Output:** `BRAINSTORM_{FEATURE}.md` with:
- Discovery questions and answers
- 2-3 approaches explored with trade-offs
- Selected approach with reasoning
- Features removed (YAGNI applied)
- Draft requirements for /define

**Process:**
1. One question at a time (never dump questions)
2. Multiple-choice preferred
3. Present 2-3 approaches with recommendation
4. Validate understanding incrementally (200-300 word sections)
5. Apply YAGNI ruthlessly

**Quality Gate:** Min 3 questions, 2+ approaches, 2+ validations, user confirmed

### Phase 1: Define

**Purpose:** Capture and validate requirements from any input.

**Input:** BRAINSTORM document, raw notes, emails, conversations, or direct requirements.

**Output:** `DEFINE_{FEATURE}.md` with:
- Problem statement
- Target users
- Success criteria (measurable)
- Acceptance tests (Given/When/Then)
- Out of scope

**Quality Gate:** Clarity Score ≥ 12/15

### Phase 2: Design

**Purpose:** Create complete technical design with inline decisions.

**Input:** `DEFINE_{FEATURE}.md`

**Output:** `DESIGN_{FEATURE}.md` with:
- Architecture diagram (ASCII)
- Key decisions with rationale
- File manifest (all files to create)
- Code patterns (copy-paste ready)
- Testing strategy

**Quality Gate:** Complete file manifest, no shared dependencies

### Phase 3: Build

**Purpose:** Execute implementation following the design.

**Input:** `DESIGN_{FEATURE}.md`

**Output:**
- Code files (as specified in manifest)
- `BUILD_REPORT_{FEATURE}.md`

**Process:**
1. Parse file manifest from DESIGN
2. Order by dependencies
3. Create each file with verification
4. Run full validation (lint, tests)

**Quality Gate:** All tasks complete, all tests pass

### Phase 4: Ship

**Purpose:** Archive completed feature with lessons learned.

**Input:** All feature artifacts

**Output:**
- `archive/{FEATURE}/` folder with all documents
- `SHIPPED_{DATE}.md` with lessons learned

---

## Key Principles

| Principle | Application |
|-----------|-------------|
| **Single Stream** | No mode switching, one unified workflow |
| **Inline Decisions** | ADRs in DESIGN document, not separate files |
| **On-the-Fly Tasks** | Tasks generated from file manifest during build |
| **Self-Contained** | Each deployable unit works independently |
| **Config Over Code** | Use YAML for configuration, not hardcoded values |
| **Iterate Anywhere** | Changes can be made at any phase via `/iterate` |

---

## Model Assignment

| Phase | Model | Rationale |
|-------|-------|-----------|
| Brainstorm | Opus | Creative thinking and nuanced dialogue |
| Define | Opus | Nuanced understanding of requirements |
| Design | Opus | Architectural decisions require depth |
| Build | Sonnet | Fast, accurate code generation |
| Ship | Haiku | Simple archival operations |
| Iterate | Sonnet | Balanced speed and understanding |

---

## References

| Resource | Location |
|----------|----------|
| Commands | `.claude/commands/workflow/` |
| Agents | `.claude/agents/workflow/` |
| Templates | `.claude/sdd/templates/` |
| Contracts | `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` |

---

## Version History

| Version | Date | Changes |
| ------- | ---- | ------- |
| 4.2.0 | 2026-01-29 | Added Agent Matching (Design) + Agent Delegation (Build) |
| 4.1.2 | 2026-01-28 | Added Sample Collection step to /brainstorm for LLM grounding |
| 4.1.0 | 2026-01-27 | Added Phase 0: /brainstorm (optional exploratory phase) |
| 4.0.0 | 2026-01-25 | Complete rewrite: 8→4 phases, single stream, inline decisions |
