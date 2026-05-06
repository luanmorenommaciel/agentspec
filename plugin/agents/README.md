# AgentSpec Agents

AgentSpec deploys **58 specialized agents** across **8 categories**, each built on a **three-tier template system** with mandatory **KB-First knowledge resolution**. Every agent carries a cognitive framework that enforces structured confidence scoring, provenance tracking, and explicit stop conditions -- turning raw LLM capability into disciplined, auditable domain expertise.

`58 agents | 8 categories | 3 tiers (T1/T2/T3) | 24 KB domains | 100% template compliance`

---

## How Agents Work (Cognitive Architecture)

AgentSpec agents are not raw LLM prompts. They operate through a three-layer cognitive architecture that separates routing, reasoning, and domain knowledge.

### Layer 1: Claude Code Orchestrator (Router)

The orchestrator is Claude Code itself. It reads all 58 agent description fields from frontmatter, pattern-matches user messages to agent capabilities, and launches the best-fit agent. The orchestrator:

- Maintains memory, tasks, and plans across messages
- Selects agents based on trigger phrases, file types, and context
- Receives structured responses with confidence scores
- Is a **generalist** -- it knows WHO to call, not HOW to do the work

### Layer 2: Agent Template (Cognitive Framework)

Every agent inherits from `_template.md`, which defines structured thinking:

- **KB-First Resolution** -- check local knowledge before external sources
- **Agreement Matrix** -- structured confidence scoring (KB vs MCP alignment)
- **Impact Tiers** -- CRITICAL/IMPORTANT/STANDARD/ADVISORY with thresholds
- **Stop Conditions** -- agents know when to REFUSE or ESCALATE
- **Provenance** -- every response cites confidence score and sources

### Layer 3: Agent Instance (Domain Specialist)

Each agent adds domain-specific knowledge, capabilities, quality gates, and anti-patterns on top of the template framework. This layer carries the expertise -- dbt, Spark, Fabric, Airflow, and so on.

### Request Flow

```text
User
  |
  v
Orchestrator (Claude Code)
  |-- reads 58 agent descriptions from frontmatter
  |-- pattern-matches message to capabilities
  |-- selects best-fit agent
  v
Agent Instance
  |-- KB-First: read ${CLAUDE_PLUGIN_ROOT}/kb/{domain}/
  |-- Agreement Matrix: calculate confidence
  |-- Impact Tier: check threshold for task type
  |-- Execute (confidence met) or Stop (below threshold)
  v
Response with Provenance
  |-- confidence score
  |-- sources cited (KB file, MCP query, codebase path)
```

---

## Agent Tiers (T1 / T2 / T3)

Every agent declares a tier in frontmatter (`tier: T1|T2|T3`). The tier governs which template sections are required and sets a line budget.

| Tier | Name | Lines | Use For |
|------|------|-------|---------|
| **T1** | Utility | 80-150 | Single-purpose tools, orchestrators, lightweight helpers |
| **T2** | Domain Expert | 150-350 | Domain specialists with KB domains, complex decision-making |
| **T3** | Platform Specialist | 350-600 | Agents with MCP dependencies, live instance access, deep platform expertise |

### Section-by-Tier Matrix

| Section | T1 | T2 | T3 |
|---------|:--:|:--:|:--:|
| Identity | Required | Required | Required |
| Knowledge Resolution | Compact | Full + Agreement Matrix | Full + Sources + Decision Tree |
| Capabilities | 2-4 | 3-5 | 3-6 |
| Constraints | -- | Required | Required |
| Stop Conditions | -- | Required | Required |
| Quality Gate | 3-5 items | 5-8 items | Multi-section |
| Response Format | Single | Standard + Below-threshold | 4-tier (high/medium/low/conflict) |
| Anti-Patterns | 3-5 rows | 5+ rows + Warning Signs | Full + Warning Signs |
| Error Recovery | -- | -- | Required |
| Extension Points | -- | -- | Required |
| Changelog | -- | -- | Required |
| Remember | Required | Required | Required |

### Current Distribution

- **T1 (10 agents):** genai-architect, medallion-architect, aws-data-architect, gcp-data-architect, ai-prompt-specialist, python-developer, lakeflow-specialist, spark-performance-analyzer, spark-troubleshooter, prompt-crafter
- **T2 (28 agents):** data-platform-engineer, kb-architect, lakehouse-architect, pipeline-architect, schema-designer, the-planner, ai-data-engineer-gcp, code-cleaner, code-documenter, code-reviewer, data-contracts-engineer, data-quality-analyst, test-generator, ai-data-engineer, dbt-specialist, spark-engineer, spark-specialist, sql-optimizer, streaming-engineer, codebase-explorer, meeting-analyst, shell-script-specialist, brainstorm-agent, build-agent, define-agent, design-agent, iterate-agent, ship-agent
- **T3 (20 agents):** ai-data-engineer-cloud, ai-prompt-specialist-gcp, aws-deployer, aws-lambda-architect, ci-cd-specialist, lambda-builder, supabase-specialist, fabric-ai-specialist, fabric-architect, fabric-cicd-specialist, fabric-logging-specialist, fabric-pipeline-developer, fabric-security-specialist, llm-specialist, airflow-specialist, lakeflow-architect, lakeflow-expert, lakeflow-pipeline-builder, qdrant-specialist, spark-streaming-architect

---

## Core Principle: KB-First Resolution

Every agent follows this mandatory knowledge resolution order. Agents that skip KB and go straight to MCP are violating the architecture.

### Resolution Order

```text
1. KB CHECK       Read ${CLAUDE_PLUGIN_ROOT}/kb/{domain}/index.md -- scan headings only (~20 lines)
2. ON-DEMAND LOAD Read specific pattern/concept file matching the task (one file, not all)
3. MCP FALLBACK   Single query if KB insufficient (max 3 MCP calls per task)
4. CONFIDENCE     Calculate from Agreement Matrix (never self-assess)
```

### Agreement Matrix

```text
                 | MCP AGREES     | MCP DISAGREES  | MCP SILENT     |
-----------------+----------------+----------------+----------------+
KB HAS PATTERN   | HIGH (0.95)    | CONFLICT(0.50) | MEDIUM (0.75)  |
                 | -> Execute     | -> Investigate | -> Proceed     |
-----------------+----------------+----------------+----------------+
KB SILENT        | MCP-ONLY(0.85) | N/A            | LOW (0.50)     |
                 | -> Proceed     |                | -> Ask User    |
```

### Impact Tiers

| Tier | Threshold | Action if Below | Examples |
|------|-----------|-----------------|----------|
| CRITICAL | 0.95 | REFUSE + explain | Schema migrations, production DDL, delete ops |
| IMPORTANT | 0.90 | ASK user first | Model creation, pipeline config, access control |
| STANDARD | 0.85 | PROCEED + caveat | Code generation, documentation |
| ADVISORY | 0.75 | PROCEED freely | Explanations, comparisons |

---

## Agent Categories

### 1. Architect (8 agents)

System-level design and architecture decisions.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `genai-architect` | T1 | opus | Multi-agent orchestration, agentic workflows, production AI systems |
| `the-planner` | T2 | opus | Strategic architecture and comprehensive implementation plans |
| `kb-architect` | T2 | sonnet | Knowledge base domain creation and audit |
| `lakehouse-architect` | T2 | sonnet | Iceberg, Delta Lake, catalog governance design |
| `medallion-architect` | T1 | sonnet | Bronze/Silver/Gold layer design, data quality progression |
| `pipeline-architect` | T2 | sonnet | Airflow, Dagster, DAG design patterns |
| `schema-designer` | T2 | sonnet | Dimensional modeling, SCD, Data Vault |
| `data-platform-engineer` | T2 | sonnet | Snowflake, Databricks, BigQuery, cost optimization |

### 2. Cloud (10 agents)

Cloud provider services, deployment, and CI/CD.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `aws-data-architect` | T1 | sonnet | Lambda, S3, Glue, Redshift, MWAA, serverless pipelines |
| `aws-deployer` | T3 | sonnet | SAM, CloudFormation, CI/CD, Terraform for AWS |
| `aws-lambda-architect` | T3 | sonnet | SAM templates, least-privilege IAM policies |
| `lambda-builder` | T3 | sonnet | Python Lambda handlers, S3-triggered functions |
| `gcp-data-architect` | T1 | sonnet | BigQuery, Cloud Run, Pub/Sub, Dataflow, Vertex AI |
| `ai-data-engineer-gcp` | T2 | sonnet | GCP serverless architectures, Cloud Functions, BigQuery pipelines |
| `ai-data-engineer-cloud` | T3 | sonnet | Cloud architecture optimization, AI/ML pipelines |
| `ai-prompt-specialist-gcp` | T3 | sonnet | Google Gemini, Vertex AI, multi-modal document extraction |
| `ci-cd-specialist` | T3 | sonnet | Azure DevOps, Terraform, Databricks Asset Bundles |
| `supabase-specialist` | T3 | opus | pgvector, RLS, Edge Functions, Auth, Realtime |

### 3. Platform (6 agents)

Microsoft Fabric specialists.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `fabric-architect` | T3 | opus | End-to-end Fabric architecture, OneLake, workload selection |
| `fabric-pipeline-developer` | T3 | sonnet | Data Factory pipelines, PySpark notebooks, Dataflow Gen2 |
| `fabric-ai-specialist` | T3 | sonnet | Fabric Copilot, ML models, AI Skills, Azure OpenAI |
| `fabric-cicd-specialist` | T3 | sonnet | Fabric CI/CD, Git integration, deployment pipelines |
| `fabric-logging-specialist` | T3 | sonnet | Workspace monitoring, KQL queries, dashboards |
| `fabric-security-specialist` | T3 | opus | RLS, permissions, data masking, encryption, compliance |

### 4. Python (6 agents)

Python development, code quality, and prompt engineering.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `python-developer` | T1 | sonnet | Python code architecture, dataclasses, type hints |
| `code-reviewer` | T2 | sonnet | Review code for quality and security issues |
| `code-cleaner` | T2 | sonnet | Clean code, remove redundant comments, apply DRY |
| `code-documenter` | T2 | sonnet | Generate documentation, READMEs, API docs |
| `ai-prompt-specialist` | T1 | sonnet | Prompt optimization, structured extraction, few-shot |
| `llm-specialist` | T3 | opus | Advanced prompt engineering, chain-of-thought, structured output |

### 5. Test (3 agents)

Testing, data quality, and contract validation.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `test-generator` | T2 | sonnet | Generate pytest tests with fixtures |
| `data-quality-analyst` | T2 | sonnet | Great Expectations, dbt tests, data contracts |
| `data-contracts-engineer` | T2 | sonnet | ODCS, SLAs, schema governance |

### 6. Data Engineering (15 agents)

Implementation specialists for data pipelines and processing.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `dbt-specialist` | T2 | sonnet | dbt models, macros, tests, incremental strategies |
| `spark-engineer` | T2 | sonnet | PySpark, Spark SQL, distributed processing |
| `spark-specialist` | T2 | opus | Spark architecture, configuration, performance |
| `spark-troubleshooter` | T1 | sonnet | Spark debugging -- OOM, data skew, shuffle failures |
| `spark-performance-analyzer` | T1 | sonnet | Spark tuning -- memory, partitions, joins, AQE |
| `spark-streaming-architect` | T3 | sonnet | Structured Streaming, Kafka, real-time pipelines |
| `streaming-engineer` | T2 | sonnet | Flink, Kafka, Spark Streaming, CDC |
| `sql-optimizer` | T2 | sonnet | Query plans, cross-dialect SQL, window functions |
| `airflow-specialist` | T3 | sonnet | Apache Airflow 3.0, DAGs, TaskFlow API |
| `lakeflow-architect` | T3 | sonnet | Databricks Lakeflow, Medallion architecture |
| `lakeflow-expert` | T3 | sonnet | DLT troubleshooting, CDC, SCD Type 2 |
| `lakeflow-pipeline-builder` | T3 | sonnet | DLT pipeline creation, quality expectations |
| `lakeflow-specialist` | T1 | sonnet | Declarative pipelines, materialized views, streaming tables |
| `ai-data-engineer` | T2 | sonnet | RAG pipelines, vector DBs, feature stores |
| `qdrant-specialist` | T3 | opus | Qdrant vector database, collection management |

### 7. Dev (4 agents)

Developer tools and productivity.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `prompt-crafter` | T1 | sonnet | SDD-lite PROMPT.md builder with agent matching |
| `codebase-explorer` | T2 | sonnet | Analyze codebase structure with health scoring |
| `meeting-analyst` | T2 | sonnet | Extract decisions and action items from meetings |
| `shell-script-specialist` | T2 | sonnet | Production-grade Bash scripts, automation, deployment scripts |

### 8. Workflow (6 agents)

Drive the SDD workflow phases.

| Agent | Tier | Model | Phase | Purpose |
|-------|------|-------|-------|---------|
| `brainstorm-agent` | T2 | sonnet | 0 | Explore ideas through collaborative dialogue |
| `define-agent` | T2 | sonnet | 1 | Capture requirements with clarity scoring |
| `design-agent` | T2 | opus | 2 | Create technical architecture with file manifest |
| `build-agent` | T2 | opus | 3 | Execute implementation with agent delegation |
| `ship-agent` | T2 | sonnet | 4 | Archive with lessons learned |
| `iterate-agent` | T2 | sonnet | All | Update documents with cascade awareness |

---

## Escalation Map

Agents are not isolated. When a task crosses domain boundaries, agents escalate to the appropriate specialist.

```text
Workflow <-> Data Engineering:
  build-agent -> dbt-specialist, spark-engineer, pipeline-architect (DE delegation)
  design-agent -> schema-designer (data modeling), pipeline-architect (DAG design)
  define-agent -> data-contracts-engineer (SLAs), data-quality-analyst (metrics)

Python <-> Data Engineering:
  code-reviewer -> sql-optimizer (SQL anti-patterns), data-quality-analyst (PII)
  code-cleaner -> dbt-specialist (CTE refactoring), sql-optimizer (query cleanup)
  test-generator -> data-quality-analyst (GE suites), dbt-specialist (dbt tests)
  python-developer -> spark-engineer (PySpark code), dbt-specialist (Python models)

Data Engineering <-> Data Engineering:
  dbt-specialist <-> spark-engineer (SQL vs PySpark)
  dbt-specialist <-> schema-designer (modeling layer)
  pipeline-architect <-> streaming-engineer (batch vs stream)
  lakehouse-architect <-> data-platform-engineer (infra decisions)
  lakeflow-specialist <-> lakehouse-architect (DLT vs generic Delta)
  medallion-architect <-> schema-designer (layer modeling)
  spark-troubleshooter <-> spark-performance-analyzer (debug vs optimize)
  ai-data-engineer <-> streaming-engineer (real-time embeddings)
  data-contracts-engineer <-> data-quality-analyst (enforcement)

Cloud <-> Data Engineering:
  aws-data-architect -> pipeline-architect (MWAA), spark-engineer (Glue)
  gcp-data-architect -> pipeline-architect (Composer), spark-engineer (Dataproc)
  fabric-architect -> medallion-architect (layer design), lakehouse-architect (Delta)
  fabric-pipeline-developer -> spark-engineer (notebooks), dbt-specialist (models)

Architect <-> Data Engineering:
  genai-architect -> ai-data-engineer (RAG data layer), streaming-engineer (real-time)
  ai-prompt-specialist -> ai-data-engineer (extraction pipelines)

Dev <-> All:
  prompt-crafter -> any agent (agent matching engine)
  shell-script-specialist -> ci-cd-specialist (CI/CD pipelines)
  codebase-explorer -> python-developer (code modifications), pipeline-architect (DE)
```

---

## When NOT to Create an Agent

Before creating a new agent, verify **all four** conditions are met:

1. **No existing agent covers >60% of this capability** -- check the escalation map above
2. **The new agent has a unique KB domain or tool combination** -- not just a renamed existing agent
3. **At least 3 distinct trigger scenarios exist** -- if fewer, it belongs as a capability of an existing agent
4. **No >80% overlap with an existing agent** -- if overlap exists, consolidate instead

If any condition fails, extend an existing agent rather than creating a new one.

---

## Creating Custom Agents

### Step-by-Step

1. **Check the "When NOT to Create" criteria** -- verify all four conditions
2. **Choose a tier** -- T1 for simple tools, T2 for domain experts, T3 for platform specialists with MCP
3. **Copy `_template.md`** to the appropriate category folder
4. **Fill in frontmatter** -- all required fields for your tier (see schema below)
5. **Write sections** required for your tier (see Section-by-Tier Matrix)
6. **Place in the correct category folder** -- architect, cloud, platform, python, test, data-engineering, dev, or workflow
7. **Verify compliance** -- all required sections present, line count within budget

### Frontmatter Schema

**Required (all tiers):**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent identifier (kebab-case, matches filename) |
| `description` | string | Purpose, trigger conditions, and 2 examples |
| `tools` | list | Available tools (Read, Write, Edit, Grep, Glob, Bash, etc.) |
| `kb_domains` | list | KB domains this agent reads (empty `[]` if none) |
| `color` | string | UI color: blue, green, orange, purple, red, or yellow |
| `tier` | string | T1, T2, or T3 |
| `anti_pattern_refs` | list | Shared anti-pattern references |

**Optional (defaults shown):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | string | sonnet | LLM model: sonnet (default), opus (complex), haiku (fast) |

**Required for T2+ only:**

| Field | Type | Description |
|-------|------|-------------|
| `stop_conditions` | list | Conditions that cause the agent to halt or refuse |
| `escalation_rules` | list | Trigger/target/reason rules for cross-agent routing |

**Optional for T3:**

| Field | Type | Description |
|-------|------|-------------|
| `mcp_servers` | list | MCP server dependencies with name, tools, and purpose |

---

## Template v2.0 Reference

All agents inherit from `_template.md`. The template defines 12 sections:

| # | Section | Purpose |
|---|---------|---------|
| 1 | **Frontmatter** | Name, description, tools, KB domains, tier, color |
| 2 | **Identity** | Purpose, domain, threshold (blockquote format) |
| 3 | **Knowledge Resolution** | KB-First order, Agreement Matrix (T2+), Sources (T3) |
| 4 | **Capabilities** | When/Process/Output for each capability |
| 5 | **Constraints** | Domain boundaries and resource limits (T2+) |
| 6 | **Stop Conditions** | Hard stops, escalation rules, retry limits (T2+) |
| 7 | **Quality Gate** | Pre-flight checklist scaled to tier |
| 8 | **Response Format** | Standard + below-threshold (T2+) + conflict/low-confidence (T3) |
| 9 | **Anti-Patterns** | Never Do / Why / Instead table + Warning Signs (T2+) |
| 10 | **Error Recovery** | Error/recovery/fallback table (T3) |
| 11 | **Extension Points** | How to extend capabilities, KB, MCP (T3) |
| 12 | **Remember** | Motto, mission, core principle |

See `_template.md` for the full template with inline comments marking tier requirements.
