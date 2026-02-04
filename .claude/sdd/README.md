# AgentSpec

> **The AI-Native Specification Framework for Claude Code**
>
> *"From Specification to Specialized Execution"*

---

## Executive Summary

| Aspect | Details |
|--------|---------|
| **Project** | AgentSpec - Spec-Driven Development Framework |
| **Tagline** | Spec-Driven Development for AI-Native Teams |
| **Business Problem** | Gap between unstructured "vibe coding" and stale traditional specifications |
| **Solution** | 5-phase workflow with 40+ AI agents and curated knowledge bases |
| **Target Audience** | AI-native development teams using Claude Code |
| **License** | MIT |

### What This Is

AgentSpec transforms requirements into working code with full traceability. It provides a structured 5-phase development workflow (Brainstorm → Define → Design → Build → Ship) powered by specialized AI agents that match to tasks automatically, grounded by curated knowledge bases for accuracy.

**The Core Insight:** *"The AI doesn't just need to know WHAT to build - it needs to know WHO should build each part."*

Traditional specs produce a task list. AgentSpec produces a **team assignment**.

### Health Score: 8.5/10

| Criterion | Score | Evidence |
|-----------|-------|----------|
| Architecture Clarity | 9/10 | Well-defined 5-phase pipeline with clear contracts |
| Agent Coverage | 9/10 | 40+ agents across 8 categories |
| KB Grounding | 8/10 | 8 domains, MCP-validated patterns |
| Documentation | 8/10 | Comprehensive but needs OSS polish |
| Extensibility | 9/10 | Framework-agnostic agent discovery |
| Testability | 7/10 | Framework needs validation tests |

### Key Insights

1. **Strength:** Automatic agent matching + KB grounding = unique differentiator vs competitors
2. **Concern:** No Judge layer to validate specs before expensive BUILD phase (planned)
3. **Opportunity:** Local telemetry can drive continuous improvement

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Key Decisions](#key-decisions)
3. [Architecture](#architecture)
4. [Key Innovations](#key-innovations)
5. [The Agent Ecosystem](#the-agent-ecosystem)
6. [Knowledge Base Integration](#knowledge-base-integration)
7. [Commands & Artifacts](#commands--artifacts)
8. [Requirements](#requirements)
9. [Open Questions](#open-questions)
10. [Success Metrics](#success-metrics)
11. [Competitive Landscape](#competitive-landscape)
12. [Anti-Patterns](#anti-patterns)
13. [Extending AgentSpec](#extending-agentspec)
14. [Quick Start](#quick-start)
15. [Stakeholders & Roles](#stakeholders--roles)
16. [Quality Verification](#quality-verification)
17. [References](#references)
18. [Version History](#version-history)

---

## Key Decisions

### Technical Decisions

| # | Decision | Rationale | Status |
|---|----------|-----------|--------|
| D1 | 5-phase pipeline (Brainstorm→Define→Design→Build→Ship) | Balances rigor with pragmatism | **Implemented** |
| D2 | Agent matching in Design phase via Glob discovery | Framework-agnostic, zero configuration | **Implemented** |
| D3 | KB grounding via Technical Context in Define | Prevents hallucinated patterns | **Implemented** |
| D4 | Model allocation: Opus (0-2), Sonnet (3), Haiku (4) | Cost/quality optimization | **Implemented** |
| D5 | Clarity Score 12/15 minimum gate | Catches incomplete specs early | **Implemented** |

### Process Decisions

| # | Decision | Rationale | Status |
|---|----------|-----------|--------|
| D6 | `/iterate` command for mid-stream changes | Maintains traceability | **Implemented** |
| D7 | Archive completed features with lessons learned | Knowledge capture | **Implemented** |
| D8 | Agent attribution in BUILD_REPORT | Clear ownership | **Implemented** |

### Planned Decisions

| # | Decision | Rationale | Status |
|---|----------|-----------|--------|
| D9 | Add LLM-as-Judge layer (Phase 1.5) | Catch errors before expensive BUILD | **Planned** |
| D10 | Multi-LLM review via OpenRouter | Diverse perspectives | **Planned** |
| D11 | Local-only telemetry (opt-in) | Privacy-first learning | **Planned** |

---

## Architecture

### The 5-Phase Pipeline

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    AGENTSPEC PIPELINE                                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────┐         │
│  │ Phase 0  │───▶│ Phase 1  │───▶│   Phase 2    │───▶│    Phase 3    │───▶│ Phase 4  │         │
│  │BRAINSTORM│    │  DEFINE  │    │    DESIGN    │    │     BUILD     │    │   SHIP   │         │
│  │(Optional)│    │          │    │              │    │               │    │          │         │
│  └────┬─────┘    └────┬─────┘    └──────┬───────┘    └───────┬───────┘    └────┬─────┘         │
│       │               │                 │                    │                 │               │
│       ▼               ▼                 ▼                    ▼                 ▼               │
│   Questions       Technical         Agent              Delegation         Archive             │
│   + Approaches    Context           Matching           + Execution        + Lessons           │
│   + YAGNI         + Clarity         + KB Lookup        + Attribution                          │
│                   Score 12/15                          + Verification                         │
│                                                                                                │
│  ◀───────────────────────────────────────────────────────────────────────────────────────────▶ │
│                                    /iterate (any phase)                                        │
│                                                                                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```text
                           ┌─────────────────────────────────────┐
                           │         .claude/kb/                 │
                           │  ┌─────┬─────┬─────┬─────┬────┐    │
                           │  │pydnt│ gcp │gemin│terra│... │    │
                           │  └──┬──┴──┬──┴──┬──┴──┬──┴────┘    │
                           └─────┼─────┼─────┼─────┼────────────┘
                                 │     │     │     │
                                 ▼     ▼     ▼     ▼
┌──────────────┐          ┌──────────────────────────────┐
│   DEFINE     │─────────▶│         KB Domains           │
│              │          │    (from Technical Context)  │
│ • Location   │          └──────────────┬───────────────┘
│ • KB Domains │                         │
│ • IaC Impact │                         ▼
└──────────────┘          ┌──────────────────────────────┐
                          │          DESIGN              │
                          │                              │
                          │  Agent Matching:             │
                          │  Glob(.claude/agents/**)     │
                          │         │                    │
                          │         ▼                    │
                          │  ┌────────────────────┐      │
                          │  │ Capability Index   │      │
                          │  │ • Keywords         │      │
                          │  │ • Roles            │      │
                          │  │ • Patterns         │      │
                          │  └─────────┬──────────┘      │
                          │            │                 │
                          │            ▼                 │
                          │  File Manifest + Agent       │
                          └──────────────┬───────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────────┐
                          │          BUILD               │
                          │                              │
                          │  For each file:              │
                          │  ┌─────────────────────┐     │
                          │  │ Has @agent-name?    │     │
                          │  └──────────┬──────────┘     │
                          │       YES   │   NO           │
                          │         ┌───┴───┐            │
                          │         ▼       ▼            │
                          │    Task()    Direct          │
                          │    Invoke    Build           │
                          │         │       │            │
                          │         └───┬───┘            │
                          │             ▼                │
                          │      BUILD_REPORT            │
                          │    + Agent Attribution       │
                          └──────────────────────────────┘
```

### Phase Details

| Phase | Command | Model | Input | Output | Quality Gate |
|-------|---------|-------|-------|--------|--------------|
| 0 | `/brainstorm` | Opus | Vague idea | BRAINSTORM_*.md | Max 5 questions, 3 approaches |
| 1 | `/define` | Opus | Requirements | DEFINE_*.md | Clarity Score >= 12/15 |
| 2 | `/design` | Opus | DEFINE doc | DESIGN_*.md | All files have agents |
| 3 | `/build` | Sonnet | DESIGN doc | Code + BUILD_REPORT | Tests pass |
| 4 | `/ship` | Haiku | All artifacts | archive/ + SHIPPED_*.md | Lessons captured |

---

## Key Innovations

### 1. Technical Context Gathering (Define Phase)

Traditional specs assume the AI knows where to put files. AgentSpec explicitly asks:

| Question | Why It Matters |
|----------|----------------|
| **Deployment Location** | Prevents misplaced files (src/ vs functions/ vs deploy/) |
| **KB Domains** | Design phase pulls correct patterns from curated knowledge |
| **IaC Impact** | Catches infrastructure needs early, triggers specialized agents |

```markdown
## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | functions/ | Cloud Run serverless |
| **KB Domains** | pydantic, gcp, gemini | LLM extraction patterns |
| **IaC Impact** | New resources | Terraform for Cloud Run + Pub/Sub |
```

### 2. Agent Matching (Design Phase)

Design dynamically discovers available agents and matches them to tasks:

```text
Step 1: Discover        Step 2: Index           Step 3: Match
──────────────────      ─────────────           ─────────────

Glob(.claude/           agents:                 main.py → @function-developer
  agents/**/*.md)         function-developer:   schema.py → @extraction-specialist
       │                    keywords: [cloud    config.yaml → @infra-deployer
       ▼                      run, serverless]  test_main.py → @test-generator
40+ agent files              role: "Cloud Run
                              developer"
```

**Framework-Agnostic:** New agents added to `.claude/agents/` automatically become available for matching - zero configuration.

### 3. Agent Delegation (Build Phase)

Build invokes matched specialists via the Task tool:

```text
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT DELEGATION                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  File Manifest:                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ main.py    │ @function-developer  │ Cloud Run pattern │     │
│  │ schema.py  │ @extraction-specialist│ Pydantic + LLM   │     │
│  │ test.py    │ @test-generator      │ pytest fixtures   │     │
│  └────────────────────────────────────────────────────────┘     │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   PARALLEL EXECUTION                      │   │
│  │                                                           │   │
│  │  Task(subagent: "function-developer", prompt: "...")     │   │
│  │  Task(subagent: "extraction-specialist", prompt: "...")  │   │
│  │  Task(subagent: "test-generator", prompt: "...")         │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  BUILD_REPORT:                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ File         │ Agent                  │ Status │ Notes │     │
│  │ main.py      │ @function-developer    │   OK   │ ...   │     │
│  │ schema.py    │ @extraction-specialist │   OK   │ ...   │     │
│  │ test.py      │ @test-generator        │   OK   │ ...   │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Agent Ecosystem

AgentSpec leverages a rich ecosystem of 40+ specialized agents:

### By Category

| Category | Count | Agents | Specialization |
|----------|-------|--------|----------------|
| **Workflow** | 6 | brainstorm, define, design, build, ship, iterate | SDD phases |
| **Code Quality** | 6 | code-reviewer, code-cleaner, test-generator, dual-reviewer, python-developer, code-documenter | Quality assurance |
| **Data Engineering** | 8 | spark-specialist, lakeflow-architect, medallion-architect, spark-troubleshooter, spark-performance-analyzer, spark-streaming-architect, lakeflow-expert, lakeflow-pipeline-builder | Data pipelines |
| **AI/ML** | 4 | llm-specialist, extraction-specialist, genai-architect, ai-prompt-specialist | LLM systems |
| **Infrastructure** | 4 | ci-cd-specialist, infra-deployer, aws-lambda-architect, lambda-builder | DevOps |
| **Communication** | 3 | adaptive-explainer, meeting-analyst, the-planner | Documentation |
| **Exploration** | 2 | codebase-explorer, kb-architect | Analysis |
| **Domain** | 5 | function-developer, pipeline-architect, dataops-builder, extraction-specialist, aws-deployer | Project-specific |

### Agent Structure

Each agent follows a standard structure for capability extraction:

```markdown
# {Agent Name}

> {One-line description} <- Used for matching

## Identity

| Attribute | Value |
|-----------|-------|
| **Role** | {Role name} <- Primary capability keyword
| **Model** | {opus/sonnet/haiku}
| ...

## Core Capabilities <- Keywords for matching

| Capability | Description |
|------------|-------------|
| **{Verb}** | {What it does}

## Process <- How it works

## Tools Available <- What it can use
```

### Agent Matching Keywords

Design phase matches agents using these keywords:

| Source | Keywords Extracted |
|--------|-------------------|
| Header description | Main purpose verbs |
| Role (Identity table) | Primary capability |
| Core Capabilities | All capability names |
| Process steps | Domain-specific terms |

**Pro tip:** Use specific keywords in your agent's description for better matching:

```markdown
# Good: "Expert in dbt transformations and Snowflake data modeling"
# Bad: "Helps with data stuff"
```

---

## Knowledge Base Integration

AgentSpec integrates deeply with the curated Knowledge Base:

### Available Domains

| Domain | Purpose | Entry Point | Status |
|--------|---------|-------------|--------|
| **pydantic** | Data validation, LLM output parsing | `.claude/kb/pydantic/` | Active |
| **gcp** | Cloud Run, Pub/Sub, GCS, BigQuery | `.claude/kb/gcp/` | Active |
| **gemini** | Document extraction, vision tasks | `.claude/kb/gemini/` | Active |
| **langfuse** | LLM observability | `.claude/kb/langfuse/` | Active |
| **terraform** | Infrastructure as Code | `.claude/kb/terraform/` | Active |
| **terragrunt** | Multi-environment orchestration | `.claude/kb/terragrunt/` | Active |
| **crewai** | Multi-agent orchestration | `.claude/kb/crewai/` | Active |
| **openrouter** | LLM fallback provider | `.claude/kb/openrouter/` | Active |

### KB Flow

```text
DEFINE                    DESIGN                    BUILD
──────                    ──────                    ─────

KB Domains:          →    Read patterns:       →    Agents consult:
• pydantic                • extraction-schema       • KB/pydantic/patterns/
• gemini                  • invoice-extraction      • KB/gemini/patterns/
• gcp                     • cloud-run-module        • KB/gcp/patterns/
```

### KB Domain Structure

```text
.claude/kb/{domain}/
├── index.md           # Domain overview
├── quick-reference.md # Cheat sheet
├── concepts/          # Core concepts
├── patterns/          # Implementation patterns
└── specs/             # YAML specifications (optional)
```

---

## Commands & Artifacts

### Commands

| Command | Phase | Purpose | Model | Input |
|---------|-------|---------|-------|-------|
| `/brainstorm` | 0 | Explore ideas through dialogue | Opus | Vague idea or topic |
| `/define` | 1 | Capture and validate requirements | Opus | Idea or BRAINSTORM doc |
| `/design` | 2 | Create architecture + agent matching | Opus | DEFINE doc |
| `/build` | 3 | Execute with agent delegation | Sonnet | DESIGN doc |
| `/ship` | 4 | Archive with lessons learned | Haiku | DEFINE doc |
| `/iterate` | Any | Update documents mid-stream | Sonnet | Any SDD doc + changes |

### Artifact Lifecycle

```text
.claude/sdd/
├── features/                          # Active work
│   ├── BRAINSTORM_{FEATURE}.md       # Phase 0 output
│   ├── DEFINE_{FEATURE}.md           # Phase 1 output
│   └── DESIGN_{FEATURE}.md           # Phase 2 output
│
├── reports/                           # Build outputs
│   └── BUILD_REPORT_{FEATURE}.md     # Phase 3 output
│
└── archive/                           # Completed work
    └── {FEATURE}/
        ├── BRAINSTORM_{FEATURE}.md   # (if used)
        ├── DEFINE_{FEATURE}.md
        ├── DESIGN_{FEATURE}.md
        ├── BUILD_REPORT_{FEATURE}.md
        └── SHIPPED_{DATE}.md         # Phase 4 output
```

### Key Artifact Sections

#### DEFINE (Technical Context)

```markdown
## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | functions/ | Cloud Run serverless |
| **KB Domains** | pydantic, gcp, gemini | Which patterns to consult |
| **IaC Impact** | New resources | Terraform changes needed |
```

#### DESIGN (Agent Assignment)

```markdown
## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | main.py | Create | Handler | @function-developer | None |
| 2 | schema.py | Create | Pydantic | @extraction-specialist | None |
| 3 | test.py | Create | Tests | @test-generator | 1, 2 |

## Agent Assignment Rationale

| Agent | Files | Why This Agent |
|-------|-------|----------------|
| @function-developer | 1 | Cloud Run patterns from KB |
| @extraction-specialist | 2 | Pydantic + LLM output validation |
| @test-generator | 3 | pytest fixtures specialist |
```

#### BUILD_REPORT (Attribution)

```markdown
## Agent Contributions

| Agent | Files | Specialization Applied |
|-------|-------|------------------------|
| @function-developer | 2 | Cloud Run, Pub/Sub handlers |
| @extraction-specialist | 2 | Pydantic models, LLM output |
| @test-generator | 2 | pytest, fixtures |
| (direct) | 1 | DESIGN patterns only |
```

---

## Requirements

### Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-001 | System must provide 5-phase SDD workflow | P0-Critical | Implemented |
| FR-002 | System must match agents to files automatically | P0-Critical | Implemented |
| FR-003 | System must ground agent responses in KB patterns | P0-Critical | Implemented |
| FR-004 | System must support `/iterate` for mid-stream changes | P1-High | Implemented |
| FR-005 | System must archive completed features with lessons | P1-High | Implemented |
| FR-006 | System must provide agent attribution in BUILD_REPORT | P1-High | Implemented |

### Non-Functional Requirements

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-001 | Define phase must enforce Clarity Score minimum | 12/15 | Implemented |
| NFR-002 | Agent discovery must be framework-agnostic | Zero config | Implemented |
| NFR-003 | KB patterns must be MCP-validated | All domains | Implemented |
| NFR-004 | Phase progression must maintain traceability | Full chain | Implemented |

### Constraints

| ID | Constraint | Type | Impact |
|----|------------|------|--------|
| C-001 | Must work with Claude Code CLI | Technical | Required |
| C-002 | Must not require external dependencies | Technical | Self-contained |
| C-003 | Agent files must follow standard structure | Convention | For matching |

### Assumptions

| ID | Assumption | Risk if Wrong | Mitigation |
|----|------------|---------------|------------|
| A-001 | Users have Claude Code CLI installed | Won't work | Document as prerequisite |
| A-002 | Users maintain KB domains | Stale patterns | Add freshness warnings |
| A-003 | Specialized agents produce better code | No benefit | Measure and compare |

---

## Open Questions

| # | Question | Context | Priority | Owner |
|---|----------|---------|----------|-------|
| Q1 | Should Judge layer be opt-in or opt-out? | User experience vs safety | HIGH | TBD |
| Q2 | How to handle agent matching confidence scores? | Edge cases need fallbacks | HIGH | TBD |
| Q3 | Should KB freshness warnings be automatic? | Stale patterns risk | MEDIUM | TBD |
| Q4 | How to measure agent quality objectively? | Need metrics | MEDIUM | TBD |
| Q5 | Should DESIGN allow manual agent override? | User control vs automation | MEDIUM | TBD |
| Q6 | How to handle circular dependencies in file manifest? | Build ordering | LOW | TBD |

---

## Success Metrics

### Framework Quality Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Agent matching accuracy | ~75% | 92% | DESIGN file audits |
| Features with full agent coverage | 60% | 95% | BUILD_REPORT analysis |
| KB freshness (< 3 months) | 85% | 95% | KB metadata |
| DEFINE→DESIGN success rate | 85% | 95% | Phase progression |
| BUILD rework rate | ~20% | <8% | Iteration tracking |

### Adoption Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Features using full pipeline | >80% | Archive count |
| Agent delegation usage | >70% | BUILD_REPORT analysis |
| KB domain utilization | >6 domains | Technical Context audit |

### Comparison: With vs Without AgentSpec

| Dimension | Without AgentSpec | With AgentSpec |
|-----------|-------------------|----------------|
| File placement | Random/guessed | Explicit in Technical Context |
| Pattern consistency | Varies | KB-grounded |
| Code ownership | Unclear | Agent attribution |
| Traceability | None | Full artifact chain |
| Specialist expertise | None | Automatic matching |

---

## Competitive Landscape

### Framework Comparison

| Dimension | Spec-Kit (GitHub) | OpenSpec (Fission-AI) | AgentSpec |
|-----------|-------------------|----------------------|-----------|
| **Philosophy** | "Specs as executable" | "Fluid not rigid" | "Who builds, not just what" |
| **Backing** | GitHub (enterprise) | Indie/startup | Claude Code ecosystem |
| **Phases** | 5 (Constitution→Implement) | 4 (new→apply→archive) | 5 (Brainstorm→Ship) |
| **Agent Awareness** | None | None | **Full orchestration** |
| **KB Grounding** | None | None | **8+ domains** |
| **Agent Matching** | None | None | **Dynamic discovery** |
| **Agent Delegation** | None | None | **Task tool invocation** |

### Positioning

```text
                    COMPLEXITY
                         │
              ┌──────────┼──────────┐
              │          │          │
              │    AgentSpec        │
         HIGH │    (orchestration)  │
              │          ▲          │
              │          │          │
              │    Spec-Kit         │
       MEDIUM │    (governance)     │
              │          ▲          │
              │          │          │
              │    OpenSpec         │
          LOW │    (pragmatic)      │
              │                     │
              └─────────────────────┘
                    TOOL-AGNOSTIC ────────► SPECIALIZED
```

### Unique Value Proposition

| Feature | Competitors | AgentSpec |
|---------|-------------|-----------|
| Agent Matching | Manual or None | **Automatic** |
| Spec Validation | None | **Judge layer (planned)** |
| KB Grounding | None | **8+ MCP-validated domains** |
| Multi-LLM Review | None | **OpenRouter (planned)** |
| Usage Analytics | None | **Local telemetry (planned)** |
| Quality Gates | Informal | **Objective, automated** |

---

## Anti-Patterns

### Never Do

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Skipping Define** | "I know what to build" | Even clear requirements benefit from Technical Context |
| **Over-Brainstorming** | 10 questions, 5 approaches | Max 5 questions, 3 approaches. Apply YAGNI |
| **Generic Agent Assignment** | All files → `(general)` | Invest in agent ecosystem |
| **Empty KB Domains** | "We don't have patterns" | Use `/create-kb` before Design |
| **Monolithic Design** | One 1000-line file | Break into files that map to single agents |
| **Skipping /iterate** | "I'll just edit the code" | Changes should flow through specs |
| **Ignoring Attribution** | Not checking BUILD_REPORT | Attribution reveals quality patterns |

### Warning Signs

```text
You're about to make a mistake if:
- You're assigning (general) to most files
- Your DEFINE has no Technical Context
- Your Clarity Score is below 12/15
- Your BUILD_REPORT has no agent attribution
- You're skipping phases "to save time"
```

### The "Just Code It" Trap

```text
WRONG                              RIGHT
─────                              ─────

"I'll just write the code"    vs    "Let me /define first"
        │                                   │
        ▼                                   ▼
   Code works but:                    Spec captures:
   • No KB patterns                   • Location decision
   • Random file location             • KB domains to use
   • No agent expertise               • Agent assignments
   • No traceability                  • Full attribution
        │                                   │
        ▼                                   ▼
   Future you: "Why is               Future you: "Oh, @extraction-
   this code here?"                  specialist built this with
                                     Pydantic patterns from KB"
```

---

## Extending AgentSpec

### Adding a New Agent

1. **Create the agent file:**

```bash
# Location: .claude/agents/{category}/{agent-name}.md
touch .claude/agents/data-engineering/dbt-specialist.md
```

2. **Follow the standard structure:**

```markdown
# DBT Specialist

> Expert in dbt transformations and data modeling

## Identity

| Attribute | Value |
|-----------|-------|
| **Role** | Data Transformation Engineer |
| **Model** | Sonnet |
| **Phase** | 3 - Build |

## Core Capabilities

| Capability | Description |
|------------|-------------|
| **Model** | Create dbt models with refs |
| **Test** | Add schema tests |
| **Document** | Generate docs |
```

3. **The agent is automatically discoverable** - Design phase will find it via `Glob(.claude/agents/**/*.md)`

### Adding a New KB Domain

1. **Create the domain structure:**

```bash
mkdir -p .claude/kb/dbt
touch .claude/kb/dbt/{index.md,quick-reference.md}
mkdir -p .claude/kb/dbt/{concepts,patterns}
```

2. **Register in KB index:**

```yaml
# .claude/kb/_index.yaml
domains:
  dbt:
    description: "dbt transformation patterns"
    entry_point: ".claude/kb/dbt/index.md"
```

3. **Reference in DEFINE Technical Context:**

```markdown
## Technical Context

| Aspect | Value |
|--------|-------|
| **KB Domains** | pydantic, dbt |  # Now available
```

---

## Quick Start

### Full Pipeline (Complex Feature)

```bash
# Phase 0: Explore the idea (optional)
/brainstorm "Build an invoice extraction system"

# Phase 1: Define requirements with Technical Context
/define .claude/sdd/features/BRAINSTORM_INVOICE_EXTRACTION.md

# Phase 2: Design with Agent Matching
/design .claude/sdd/features/DEFINE_INVOICE_EXTRACTION.md

# Phase 3: Build with Agent Delegation
/build .claude/sdd/features/DESIGN_INVOICE_EXTRACTION.md

# Phase 4: Archive
/ship .claude/sdd/features/DEFINE_INVOICE_EXTRACTION.md
```

### Clear Requirements (Skip Brainstorm)

```bash
# Phase 1: Define directly
/define "Build a REST API endpoint for user authentication"

# Continue: /design → /build → /ship
```

### Mid-Stream Changes

```bash
# Update any phase
/iterate DEFINE_AUTH.md "Add OAuth support requirement"
/iterate DESIGN_AUTH.md "Change to use JWT tokens"
```

### Decision Flowchart

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    SHOULD I USE AGENTSPEC?                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Start: "I need to build something"                                  │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────┐                                     │
│  │ Is it complex?              │                                     │
│  │ (> 3 files, multi-component)│                                     │
│  └─────────────┬───────────────┘                                     │
│           YES  │  NO                                                 │
│         ┌──────┴──────┐                                              │
│         ▼             ▼                                              │
│    AgentSpec     Direct coding                                       │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────┐                                     │
│  │ Idea clear or vague?        │                                     │
│  └─────────────┬───────────────┘                                     │
│        CLEAR   │  VAGUE                                              │
│         ┌──────┴──────┐                                              │
│         ▼             ▼                                              │
│     /define      /brainstorm                                         │
│                       │                                              │
│                       ▼                                              │
│                   /define                                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Stakeholders & Roles

### For AgentSpec Usage

| Role | Responsibilities | Commands Used |
|------|------------------|---------------|
| **Product Owner** | Define requirements, approve DEFINE | `/define`, review DEFINE_*.md |
| **Tech Lead** | Review DESIGN, approve architecture | `/design`, review DESIGN_*.md |
| **Developer** | Execute BUILD, verify results | `/build`, `/iterate` |
| **Team** | Archive and capture lessons | `/ship`, review archive/ |

### RACI Matrix (Per Feature)

| Activity | Product Owner | Tech Lead | Developer |
|----------|---------------|-----------|-----------|
| Brainstorm | R/A | C | C |
| Define requirements | R/A | C | I |
| Design architecture | C | R/A | C |
| Build implementation | I | C | R/A |
| Ship and archive | I | A | R |

**Legend:** R = Responsible, A = Accountable, C = Consulted, I = Informed

---

## Quality Verification

### Document Quality Checklist

Run before finalizing any SDD document:

```text
COMPLETENESS
[ ] All required sections present
[ ] Technical Context filled (DEFINE)
[ ] Agent assignments complete (DESIGN)
[ ] Attribution documented (BUILD_REPORT)

ACCURACY
[ ] Clarity Score >= 12/15 (DEFINE)
[ ] All files have agents (DESIGN)
[ ] Dependencies mapped (DESIGN)
[ ] Tests verified (BUILD)

TRACEABILITY
[ ] Phase progression documented
[ ] Cross-references valid
[ ] Lessons captured (SHIPPED)
```

### Agent Quality Checklist

```text
STRUCTURE
[ ] Has name, description in frontmatter
[ ] Has Identity table with Role
[ ] Has Core Capabilities section
[ ] Has Process section
[ ] Has Tools Available section

CONTENT
[ ] Description has matching keywords
[ ] Examples are realistic
[ ] Anti-patterns documented
```

### KB Domain Quality Checklist

```text
STRUCTURE
[ ] Has index.md with overview
[ ] Has quick-reference.md
[ ] Has concepts/ folder
[ ] Has patterns/ folder

CONTENT
[ ] MCP validated
[ ] Freshness date recorded
[ ] Cross-references work
[ ] Code examples tested
```

---

## References

| Resource | Location |
|----------|----------|
| SDD Index | `.claude/sdd/_index.md` |
| Agents | `.claude/agents/` |
| Knowledge Base | `.claude/kb/` |
| Commands | `.claude/commands/workflow/` |
| Templates | `.claude/sdd/templates/` |
| Examples | `.claude/sdd/examples/` |
| Archive | `.claude/sdd/archive/` |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 4.3.0 | 2026-02-03 | Restructured with meeting-analyst + codebase-explorer + code-documenter frameworks; Removed Dev Loop to focus on SDD |
| 4.2.0 | 2026-01-29 | Added Agent Matching + Delegation |
| 4.1.2 | 2026-01-28 | Added Sample Collection to /brainstorm |
| 4.1.0 | 2026-01-27 | Added Phase 0: /brainstorm |
| 4.0.0 | 2026-01-25 | Complete rewrite: 8→5 phases |

---

## The Agentic-First Vision

AgentSpec is designed for a future where:

1. **AI models are specialists** - Not one-size-fits-all, but domain experts
2. **Specifications are executable** - Not just documentation, but orchestration
3. **Quality comes from expertise** - Specialists produce better code than generalists
4. **Knowledge is curated** - Patterns validated by MCP, not hallucinated
5. **Traceability is automatic** - Every file has an owner, every decision has rationale

**AgentSpec is not just a specification framework. It's an AI team orchestration system.**

```text
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   "Tell me WHAT to build, I'll figure out WHO should build it"  │
│                                                                  │
│                         — AgentSpec                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

*Document Restructured: 2026-02-03*
*Frameworks Applied: Meeting Analyst (10-section), Codebase Explorer (Executive Summary), Code Documenter (Quality Checklists)*
