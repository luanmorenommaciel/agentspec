# AgentSpec

> **Spec-Driven Development Framework for Data Engineering on Claude Code**
>
> *"From Specification to Specialized Execution"*

---

## Executive Summary

| Aspect | Details |
|--------|---------|
| **Project** | AgentSpec - Spec-Driven Development Framework |
| **Tagline** | Spec-Driven Development for Data Engineering |
| **Business Problem** | Gap between unstructured "vibe coding" and stale traditional specifications |
| **Solution** | 5-phase workflow with 58 specialized AI agents, 23 KB domains, and 30 commands |
| **Target Audience** | Data engineering teams using Claude Code |
| **License** | MIT |

### What This Is

AgentSpec transforms requirements into working code with full traceability. It provides a structured 5-phase development workflow (Brainstorm -> Define -> Design -> Build -> Ship) powered by specialized AI agents that match to tasks automatically, grounded by curated knowledge bases for accuracy.

**The Core Insight:** *"The AI doesn't just need to know WHAT to build - it needs to know WHO should build each part."*

Traditional specs produce a task list. AgentSpec produces a **team assignment**.

### Key Insights

1. **Strength:** Automatic agent matching + KB grounding = unique differentiator vs competitors
2. **Strength:** Deep data engineering specialization (dbt, Spark, Airflow, Flink, Iceberg, medallion architecture)
3. **Concern:** No Judge layer to validate specs before expensive BUILD phase (planned)
4. **Opportunity:** Local telemetry can drive continuous improvement

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
11. [Anti-Patterns](#anti-patterns)
12. [Extending AgentSpec](#extending-agentspec)
13. [Quick Start](#quick-start)
14. [Quality Verification](#quality-verification)
15. [References](#references)
16. [Version History](#version-history)

---

## Key Decisions

### Technical Decisions

| # | Decision | Rationale | Status |
|---|----------|-----------|--------|
| D1 | 5-phase pipeline (Brainstorm->Define->Design->Build->Ship) | Balances rigor with pragmatism | **Implemented** |
| D2 | Agent matching in Design phase via Glob discovery | Framework-agnostic, zero configuration | **Implemented** |
| D3 | KB grounding via Technical Context in Define | Prevents hallucinated patterns | **Implemented** |
| D4 | Model allocation: Opus (0-2), Sonnet (3), Haiku (4) | Cost/quality optimization | **Implemented** |
| D5 | Clarity Score 12/15 minimum gate | Catches incomplete specs early | **Implemented** |
| D6 | Data engineering specialization across agents, KB, and commands | Deep domain expertise for DE workflows | **Implemented** |

### Process Decisions

| # | Decision | Rationale | Status |
|---|----------|-----------|--------|
| D7 | `/iterate` command for mid-stream changes | Maintains traceability | **Implemented** |
| D8 | Archive completed features with lessons learned | Knowledge capture | **Implemented** |
| D9 | Agent attribution in BUILD_REPORT | Clear ownership | **Implemented** |

### Planned Decisions

| # | Decision | Rationale | Status |
|---|----------|-----------|--------|
| D10 | Add LLM-as-Judge layer (Phase 1.5) | Catch errors before expensive BUILD | **Planned** |
| D11 | Multi-LLM review via OpenRouter | Diverse perspectives | **Planned** |
| D12 | Local-only telemetry (opt-in) | Privacy-first learning | **Planned** |

---

## Architecture

### The 5-Phase Pipeline

```text
+---------------------------------------------------------------------------------------------------------+
|                                    AGENTSPEC PIPELINE                                                    |
+---------------------------------------------------------------------------------------------------------+
|                                                                                                          |
|  +----------+    +----------+    +--------------+    +---------------+    +----------+                   |
|  | Phase 0  |--->| Phase 1  |--->|   Phase 2    |--->|    Phase 3    |--->| Phase 4  |                   |
|  |BRAINSTORM|    |  DEFINE  |    |    DESIGN    |    |     BUILD     |    |   SHIP   |                   |
|  |(Optional)|    |          |    |              |    |               |    |          |                   |
|  +----+-----+    +----+-----+    +------+-------+    +-------+-------+    +----+-----+                   |
|       |               |                 |                    |                 |                          |
|       v               v                 v                    v                 v                          |
|   Questions       Technical         Agent              Delegation         Archive                        |
|   + Approaches    Context           Matching           + Execution        + Lessons                      |
|   + YAGNI         + Clarity         + KB Lookup        + Attribution                                     |
|                   Score 12/15                          + Verification                                    |
|                                                                                                          |
|  <-------------------------------------------------------------------------->                            |
|                                    /iterate (any phase)                                                  |
|                                                                                                          |
+---------------------------------------------------------------------------------------------------------+
```

### Data Flow

```text
                           +-------------------------------------+
                           |         ${CLAUDE_PLUGIN_ROOT}/kb/                 |
                           |  +------------------------------+   |
                           |  |  23 curated KB domains       |   |
                           |  |  (dbt, Spark, Airflow, ...)  |   |
                           |  +------------------------------+   |
                           +------------------+------------------+
                                              |
                                              v
+------------------+         +------------------------------+
|   DEFINE         |-------->|         KB Domains           |
|                  |         |    (from Technical Context)  |
| - Location       |         +------------------------------+
| - KB Domains     |                        |
| - IaC Impact     |                        v
| - Data Lineage   |         +------------------------------+
+------------------+         |          DESIGN              |
                             |                              |
                             |  Agent Matching:             |
                             |  Glob(${CLAUDE_PLUGIN_ROOT}/agents/**)     |
                             |         |                    |
                             |         v                    |
                             |  +--------------------+      |
                             |  | Capability Index   |      |
                             |  | - Keywords         |      |
                             |  | - Roles            |      |
                             |  | - Patterns         |      |
                             |  +--------------------+      |
                             |            |                 |
                             |            v                 |
                             |  File Manifest + Agent       |
                             +------------------------------+
                                            |
                                            v
                             +------------------------------+
                             |          BUILD               |
                             |                              |
                             |  For each file:              |
                             |  Has @agent-name?            |
                             |       YES     NO             |
                             |         |       |            |
                             |         v       v            |
                             |    Task()    Direct          |
                             |    Invoke    Build           |
                             |         |       |            |
                             |         v       v            |
                             |      BUILD_REPORT            |
                             |    + Agent Attribution       |
                             +------------------------------+
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
| **Deployment Location** | Prevents misplaced files (models/ vs functions/ vs deploy/) |
| **KB Domains** | Design phase pulls correct patterns from curated knowledge |
| **IaC Impact** | Catches infrastructure needs early, triggers specialized agents |
| **Data Lineage** | Maps upstream/downstream dependencies for pipeline design |

```markdown
## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | models/staging/ | dbt staging models |
| **KB Domains** | dbt, sql-patterns, data-modeling | Patterns to consult |
| **IaC Impact** | None | No infrastructure changes |
| **Data Lineage** | raw.orders -> stg_orders | Source to target mapping |
```

### 2. Agent Matching (Design Phase)

Design dynamically discovers available agents and matches them to tasks:

```text
Step 1: Discover        Step 2: Index           Step 3: Match
------------------      -------------           -------------

Glob(agents/             agents:                 stg_orders.sql -> @dbt-specialist
  **/*.md)                dbt-specialist:       spark_job.py -> @spark-engineer
       |                    keywords: [dbt,     quality.py -> @data-quality-analyst
       v                      model, staging]   dag.py -> @airflow-specialist
58 agent files              role: "Data
                              Transformation
                              Engineer"
```

**Framework-Agnostic:** New agents added to `${CLAUDE_PLUGIN_ROOT}/agents/` automatically become available for matching -- zero configuration.

### 3. Agent Delegation (Build Phase)

Build invokes matched specialists via the Task tool:

```text
+-------------------------------------------------------------+
|                    AGENT DELEGATION                          |
+-------------------------------------------------------------+
|                                                              |
|  File Manifest:                                              |
|  +--------------------------------------------------------+ |
|  | stg_orders.sql  | @dbt-specialist    | staging model   | |
|  | spark_job.py    | @spark-engineer    | transformation  | |
|  | test_quality.py | @test-generator    | pytest suite    | |
|  +--------------------------------------------------------+ |
|                          |                                   |
|                          v                                   |
|  +--------------------------------------------------------+ |
|  |                   PARALLEL EXECUTION                    | |
|  |                                                         | |
|  |  Task(subagent: "dbt-specialist", prompt: "...")       | |
|  |  Task(subagent: "spark-engineer", prompt: "...")       | |
|  |  Task(subagent: "test-generator", prompt: "...")       | |
|  +--------------------------------------------------------+ |
|                          |                                   |
|                          v                                   |
|  BUILD_REPORT:                                               |
|  +--------------------------------------------------------+ |
|  | File             | Agent              | Status | Notes  | |
|  | stg_orders.sql   | @dbt-specialist    |   OK   | ...    | |
|  | spark_job.py     | @spark-engineer    |   OK   | ...    | |
|  | test_quality.py  | @test-generator    |   OK   | ...    | |
|  +--------------------------------------------------------+ |
|                                                              |
+-------------------------------------------------------------+
```

---

## The Agent Ecosystem

AgentSpec leverages an ecosystem of **58 specialized agents** across 8 categories:

### By Category

| Category | Count | Key Agents | Specialization |
|----------|-------|------------|----------------|
| **Workflow** | 6 | brainstorm, define, design, build, ship, iterate | SDD phase execution |
| **Architect** | 8 | schema-designer, pipeline-architect, medallion-architect, lakehouse-architect, genai-architect, the-planner, data-platform-engineer, kb-architect | System-level design |
| **Cloud** | 10 | aws-data-architect, aws-deployer, aws-lambda-architect, gcp-data-architect, ai-data-engineer-cloud, ai-data-engineer-gcp, ai-prompt-specialist-gcp, lambda-builder, ci-cd-specialist, supabase-specialist | Cloud infrastructure |
| **Platform** | 6 | fabric-architect, fabric-pipeline-developer, fabric-security-specialist, fabric-cicd-specialist, fabric-logging-specialist, fabric-ai-specialist | Microsoft Fabric |
| **Python** | 6 | python-developer, code-reviewer, code-cleaner, code-documenter, llm-specialist, ai-prompt-specialist | Code quality and prompts |
| **Test** | 3 | test-generator, data-quality-analyst, data-contracts-engineer | Quality assurance |
| **Data Engineering** | 15 | dbt-specialist, spark-engineer, spark-specialist, spark-troubleshooter, spark-performance-analyzer, spark-streaming-architect, sql-optimizer, streaming-engineer, airflow-specialist, lakeflow-specialist, lakeflow-expert, lakeflow-architect, lakeflow-pipeline-builder, ai-data-engineer, qdrant-specialist | DE implementation |
| **Dev** | 4 | prompt-crafter, codebase-explorer, shell-script-specialist, meeting-analyst | Developer productivity |

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

---

## Knowledge Base Integration

AgentSpec integrates deeply with 23 curated Knowledge Base domains:

### Available Domains

| Domain | Focus |
|--------|-------|
| dbt | Transformations, incremental strategies, testing, mesh |
| spark | DataFrames, Catalyst optimizer, read/write patterns |
| sql-patterns | Window functions, CTEs, cross-dialect, deduplication |
| airflow | DAG design, operators, sensors, dynamic task mapping |
| streaming | Flink, Kafka, CDC patterns, streaming databases |
| data-modeling | Star schema, Data Vault, SCD, normalization |
| data-quality | Great Expectations, Soda, observability, contracts |
| lakehouse | Iceberg, Delta Lake, DuckLake, catalogs |
| medallion | Bronze/Silver/Gold layers, data quality gates |
| lakeflow | Databricks DLT, serverless pipelines |
| cloud-platforms | Snowflake, Databricks, BigQuery |
| aws | Lambda, S3, Glue, SAM |
| gcp | Cloud Run, Pub/Sub, BigQuery |
| microsoft-fabric | Lakehouse, Warehouse, Pipelines, AI |
| modern-stack | DuckDB, Polars, SQLMesh |
| ai-data-engineering | RAG, vector DBs, feature stores, LLMOps |
| prompt-engineering | Chain-of-thought, extraction, structured output |
| genai | Multi-agent systems, guardrails, tool calling |
| pydantic | Validation, LLM output schemas |
| python | Dataclasses, type hints, clean architecture |
| testing | pytest, fixtures, integration tests |
| terraform | Modules, state, workspaces |

Domains are registered in `${CLAUDE_PLUGIN_ROOT}/kb/_index.yaml`. Use `/create-kb` to add new domains.

### KB Flow

```text
DEFINE                    DESIGN                    BUILD
------                    ------                    -----

KB Domains:          ->    Read patterns:       ->    Agents consult:
- dbt                      - incremental-model       - KB/dbt/patterns/
- sql-patterns             - cross-dialect            - KB/sql-patterns/patterns/
- data-modeling            - star-schema              - KB/data-modeling/patterns/
```

### KB Domain Structure

```text
${CLAUDE_PLUGIN_ROOT}/kb/{domain}/
+-- index.md           # Domain overview
+-- quick-reference.md # Cheat sheet
+-- concepts/          # Core concepts (3-6 files)
+-- patterns/          # Implementation patterns (3-6 files)
+-- specs/             # YAML specifications (optional)
```

---

## Commands & Artifacts

### All Commands (21)

#### SDD Workflow (7)

| Command | Phase | Purpose | Model |
|---------|-------|---------|-------|
| `/brainstorm` | 0 | Explore ideas through collaborative dialogue | Opus |
| `/define` | 1 | Capture and validate requirements | Opus |
| `/design` | 2 | Create architecture + agent matching | Opus |
| `/build` | 3 | Execute with agent delegation | Sonnet |
| `/ship` | 4 | Archive with lessons learned | Haiku |
| `/iterate` | Any | Update documents mid-stream | Sonnet |
| `/create-pr` | -- | Create pull request with conventional commits | -- |

#### Data Engineering (8)

| Command | Purpose |
|---------|---------|
| `/pipeline` | DAG/pipeline scaffolding |
| `/schema` | Interactive schema design (star schema, Data Vault, SCD) |
| `/data-quality` | Quality rules generation (Great Expectations, Soda) |
| `/lakehouse` | Table format and catalog guidance (Iceberg, Delta) |
| `/sql-review` | SQL-specific code review |
| `/ai-pipeline` | RAG/embedding pipeline scaffolding |
| `/data-contract` | Contract authoring (ODCS) |
| `/migrate` | Legacy ETL migration |

#### Core & Utilities (6)

| Command | Purpose |
|---------|---------|
| `/create-kb` | Create a complete KB domain from scratch |
| `/review` | Dual AI code review |
| `/meeting` | Meeting transcript analysis |
| `/memory` | Save session insights to storage |
| `/sync-context` | Update CLAUDE.md from codebase |
| `/readme-maker` | Generate README from codebase analysis |

### Artifact Lifecycle

```text
.claude/sdd/
+-- features/                          # Active work
|   +-- BRAINSTORM_{FEATURE}.md       # Phase 0 output
|   +-- DEFINE_{FEATURE}.md           # Phase 1 output
|   +-- DESIGN_{FEATURE}.md           # Phase 2 output
|
+-- reports/                           # Build outputs
|   +-- BUILD_REPORT_{FEATURE}.md     # Phase 3 output
|
+-- archive/                           # Completed work
    +-- {FEATURE}/
        +-- BRAINSTORM_{FEATURE}.md   # (if used)
        +-- DEFINE_{FEATURE}.md
        +-- DESIGN_{FEATURE}.md
        +-- BUILD_REPORT_{FEATURE}.md
        +-- SHIPPED_{DATE}.md         # Phase 4 output
```

### Key Artifact Sections

#### DEFINE (Technical Context)

```markdown
## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | models/staging/ | dbt staging models |
| **KB Domains** | dbt, sql-patterns | Patterns to consult |
| **IaC Impact** | None | No infrastructure changes |
| **Data Lineage** | raw.orders -> stg_orders | Source to target |
```

#### DESIGN (Agent Assignment)

```markdown
## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | models/staging/stg_orders.sql | Create | Staging model | @dbt-specialist | None |
| 2 | models/marts/fct_orders.sql | Create | Fact table | @dbt-specialist | 1 |
| 3 | tests/test_orders.py | Create | Quality tests | @data-quality-analyst | 1, 2 |

## Agent Assignment Rationale

| Agent | Files | Why This Agent |
|-------|-------|----------------|
| @dbt-specialist | 1, 2 | dbt model patterns from KB |
| @data-quality-analyst | 3 | Great Expectations suite |
```

#### BUILD_REPORT (Attribution)

```markdown
## Agent Contributions

| Agent | Files | Specialization Applied |
|-------|-------|------------------------|
| @dbt-specialist | 2 | Incremental models, refs, schema tests |
| @data-quality-analyst | 1 | Great Expectations suite |
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
| FR-007 | System must provide data engineering-specific commands | P1-High | Implemented |
| FR-008 | System must include curated DE knowledge base domains | P1-High | Implemented |

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

---

## Open Questions

| # | Question | Context | Priority |
|---|----------|---------|----------|
| Q1 | Should Judge layer be opt-in or opt-out? | User experience vs safety | HIGH |
| Q2 | How to handle agent matching confidence scores? | Edge cases need fallbacks | HIGH |
| Q3 | Should KB freshness warnings be automatic? | Stale patterns risk | MEDIUM |
| Q4 | How to measure agent quality objectively? | Need metrics | MEDIUM |
| Q5 | Should DESIGN allow manual agent override? | User control vs automation | MEDIUM |

---

## Success Metrics

### Framework Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Agent matching accuracy | 92% | DESIGN file audits |
| Features with full agent coverage | 95% | BUILD_REPORT analysis |
| KB freshness (< 3 months) | 95% | KB metadata |
| DEFINE->DESIGN success rate | 95% | Phase progression |
| BUILD rework rate | <8% | Iteration tracking |

### Comparison: With vs Without AgentSpec

| Dimension | Without AgentSpec | With AgentSpec |
|-----------|-------------------|----------------|
| File placement | Random/guessed | Explicit in Technical Context |
| Pattern consistency | Varies | KB-grounded (23 domains) |
| Code ownership | Unclear | Agent attribution (58 agents) |
| Traceability | None | Full artifact chain |
| Specialist expertise | None | Automatic matching |
| Data lineage | Manual | Captured in Define phase |

---

## Anti-Patterns

### Never Do

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Skipping Define** | "I know what to build" | Even clear requirements benefit from Technical Context |
| **Over-Brainstorming** | 10 questions, 5 approaches | Max 5 questions, 3 approaches. Apply YAGNI |
| **Generic Agent Assignment** | All files -> `(general)` | Invest in agent ecosystem |
| **Empty KB Domains** | "We don't have patterns" | Use `/create-kb` before Design |
| **Monolithic Design** | One 1000-line file | Break into files that map to single agents |
| **Skipping /iterate** | "I'll just edit the code" | Changes should flow through specs |
| **Ignoring Attribution** | Not checking BUILD_REPORT | Attribution reveals quality patterns |
| **SELECT * in production** | Missing columns, bloated scans | Always expand to explicit columns |

### Warning Signs

```text
You're about to make a mistake if:
- You're assigning (general) to most files
- Your DEFINE has no Technical Context
- Your Clarity Score is below 12/15
- Your BUILD_REPORT has no agent attribution
- You're skipping phases "to save time"
- Your SQL has no partition filters on large tables
```

---

## Extending AgentSpec

### Adding a New Agent

1. **Create the agent file:**

```bash
# Location: ${CLAUDE_PLUGIN_ROOT}/agents/{category}/{agent-name}.md
touch ${CLAUDE_PLUGIN_ROOT}/agents/data-engineering/iceberg-specialist.md
```

2. **Follow the standard structure:**

```markdown
# Iceberg Specialist

> Expert in Apache Iceberg table format, partition evolution, and catalog management

## Identity

| Attribute | Value |
|-----------|-------|
| **Role** | Table Format Engineer |
| **Model** | Sonnet |
| **Phase** | 3 - Build |

## Core Capabilities

| Capability | Description |
|------------|-------------|
| **Partition** | Design and evolve partition strategies |
| **Compact** | Optimize table maintenance and compaction |
| **Migrate** | Convert between table formats |
```

3. **The agent is automatically discoverable** -- Design phase will find it via `Glob(${CLAUDE_PLUGIN_ROOT}/agents/**/*.md)`

### Adding a New KB Domain

1. **Use the command:**

```bash
/create-kb "iceberg"
```

2. **Or manually create the structure:**

```bash
mkdir -p ${CLAUDE_PLUGIN_ROOT}/kb/iceberg/{concepts,patterns}
touch ${CLAUDE_PLUGIN_ROOT}/kb/iceberg/{index.md,quick-reference.md}
```

3. **Register in KB index** (`${CLAUDE_PLUGIN_ROOT}/kb/_index.yaml`):

```yaml
domains:
  iceberg:
    description: "Apache Iceberg table format patterns"
    entry_point: "${CLAUDE_PLUGIN_ROOT}/kb/iceberg/index.md"
```

4. **Reference in DEFINE Technical Context:**

```markdown
| **KB Domains** | iceberg, lakehouse |
```

---

## Quick Start

### Full Pipeline (Data Engineering Feature)

```bash
# Phase 0: Explore the idea (optional)
/brainstorm "Build an incremental orders pipeline with SCD Type 2"

# Phase 1: Define requirements with Technical Context
/define .claude/sdd/features/BRAINSTORM_ORDERS_PIPELINE.md

# Phase 2: Design with Agent Matching
/design .claude/sdd/features/DEFINE_ORDERS_PIPELINE.md

# Phase 3: Build with Agent Delegation
/build .claude/sdd/features/DESIGN_ORDERS_PIPELINE.md

# Phase 4: Archive
/ship .claude/sdd/features/DEFINE_ORDERS_PIPELINE.md
```

### Using DE-Specific Commands

```bash
# Design a star schema
/schema "Star schema for e-commerce analytics"

# Scaffold a pipeline
/pipeline "Daily orders ETL from Postgres to Snowflake"

# Generate quality checks
/data-quality models/staging/stg_orders.sql

# Author a data contract
/data-contract "orders dataset for analytics team"
```

### Making Changes Mid-Stream

```bash
# Update DEFINE with new requirement
/iterate DEFINE_ORDERS_PIPELINE.md "Add support for late-arriving facts"

# Update DESIGN with architecture change
/iterate DESIGN_ORDERS_PIPELINE.md "Switch from full refresh to incremental"
```

---

## Quality Verification

### Document Quality Checklist

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

### Data Engineering Quality Checklist

```text
SQL QUALITY
[ ] sqlfluff lint passes (0 violations)
[ ] No SELECT * in production models
[ ] Explicit type casts in joins
[ ] Partition filters on large tables

DATA QUALITY
[ ] unique + not_null on primary keys
[ ] Relationships on foreign keys
[ ] Source freshness within SLA
[ ] PII columns tagged and masked

SCHEMA GOVERNANCE
[ ] No breaking changes without deprecation
[ ] Data contract published for consumers
[ ] Lineage documented in Technical Context
```

---

## References

| Resource | Location |
|----------|----------|
| SDD Index | `${CLAUDE_PLUGIN_ROOT}/sdd/_index.md` |
| Architecture | `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/ARCHITECTURE.md` |
| Workflow Contracts | `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml` |
| Templates | `${CLAUDE_PLUGIN_ROOT}/sdd/templates/` |
| Archive | `.claude/sdd/archive/` |
| Agents (58) | `${CLAUDE_PLUGIN_ROOT}/agents/` |
| Knowledge Base (23) | `${CLAUDE_PLUGIN_ROOT}/kb/` |
| SDD Commands | `${CLAUDE_PLUGIN_ROOT}/commands/workflow/` |
| DE Commands | `${CLAUDE_PLUGIN_ROOT}/commands/data-engineering/` |
| Core Commands | `${CLAUDE_PLUGIN_ROOT}/commands/core/` |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2026-03-26 | Multi-cloud coverage: 58 agents across 8 categories, 23 KB domains |
| 2.0.0 | 2026-03-26 | Data engineering pivot: 11 KB domains, 11 DE agents, 8 DE commands |
| 1.0.0 | 2026-02-17 | Public release as AgentSpec v1.0.0 with 16 agents |

---

## The Agentic-First Vision

AgentSpec is designed for a future where:

1. **AI models are specialists** -- Not one-size-fits-all, but domain experts
2. **Specifications are executable** -- Not just documentation, but orchestration
3. **Quality comes from expertise** -- Specialists produce better code than generalists
4. **Knowledge is curated** -- Patterns validated by MCP, not hallucinated
5. **Traceability is automatic** -- Every file has an owner, every decision has rationale
6. **Data engineering is first-class** -- Pipelines, schemas, and quality are built-in concerns

**AgentSpec is not just a specification framework. It's an AI team orchestration system for data engineering.**

```text
+-------------------------------------------------------------+
|                                                               |
|   "Tell me WHAT to build, I'll figure out WHO should         |
|    build it -- with the right data engineering patterns."    |
|                                                               |
|                         -- AgentSpec v2.1                     |
|                                                               |
+-------------------------------------------------------------+
```

---

*Document Updated: 2026-03-26 | AgentSpec v2.1.0*
