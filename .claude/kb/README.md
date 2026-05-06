# AgentSpec Knowledge Base

> The structured knowledge layer that grounds every agent response in verified, domain-specific content.

```
24 domains | 289 files | 42,500+ lines | MCP-validated 2026-03-26
```

---

## How KB Works — KB-First Architecture

Every AgentSpec agent follows **KB-First Resolution**: local knowledge is always checked before external sources. This is mandatory, not optional.

### Resolution Order

```text
1. KB CHECK        Agent reads index.md of the relevant domain (headings only)
2. ON-DEMAND LOAD  Agent reads specific concept or pattern file matching the task
3. MCP FALLBACK    Only if KB content is insufficient (max 3 MCP calls)
4. CONFIDENCE      Calculated from the Agreement Matrix below
```

### Agreement Matrix

Confidence is determined by how KB content and MCP responses align:

```text
                  | MCP AGREES      | MCP DISAGREES   | MCP SILENT      |
------------------+-----------------+-----------------+-----------------+
KB HAS PATTERN    | HIGH (0.95)     | CONFLICT (0.50) | MEDIUM (0.75)   |
KB SILENT         | MCP-ONLY (0.85) | N/A             | LOW (0.50)      |
```

When confidence falls below an agent's threshold (typically 0.90-0.95), the agent must ask the user for clarification rather than guessing.

---

## Domain Structure

Every KB domain follows this standard layout:

```text
{domain}/
  index.md              Domain overview and navigation
  quick-reference.md    Fast lookup tables (~100 lines)
  concepts/             Core concepts (3-6 files, ~150 lines each)
    concept-1.md
    concept-2.md
  patterns/             Implementation patterns (3-6 files, ~200 lines each)
    pattern-1.md
    pattern-2.md
```

Some domains extend this with additional directories:

- `reference/` -- Reference material with no line limit (e.g., lakeflow)
- Numbered sub-domains -- Organized topic areas (e.g., microsoft-fabric `01-logging-monitoring/`)
- Sub-domain directories -- Nested specializations (e.g., aws `lambda/`, `deployment/`)

---

## Domain Catalog

### Core Data Engineering

| Domain | Files | Description | Used By |
|--------|------:|-------------|---------|
| dbt | 12 | Fusion Engine, Mesh, Semantic Layer, models, macros, tests | dbt-specialist, code-reviewer, sql-optimizer, test-generator, data-quality-analyst, pipeline-architect |
| spark | 11 | PySpark, Spark SQL, DataFrames, Real-Time Mode, Spark Connect | spark-engineer, spark-specialist, spark-streaming-architect, spark-troubleshooter, spark-performance-analyzer, lakehouse-architect, lakeflow-architect |
| airflow | 10 | Airflow 3.x TaskFlow, Dagster, Prefect comparison, DAG design | airflow-specialist, pipeline-architect |
| sql-patterns | 9 | Cross-dialect SQL: window functions, CTEs, deduplication | code-reviewer, sql-optimizer, spark-engineer, spark-specialist, spark-troubleshooter, streaming-engineer, airflow-specialist, schema-designer |
| streaming | 10 | Flink, Kafka, Spark Streaming, RisingWave, Materialize, CDC | streaming-engineer, spark-streaming-architect, ai-data-engineer |
| data-modeling | 10 | Dimensional modeling, Data Vault, SCD types, schema evolution | schema-designer, data-platform-engineer, medallion-architect, supabase-specialist, data-contracts-engineer, data-quality-analyst, sql-optimizer |
| data-quality | 10 | Soda, Great Expectations, dbt tests, ODCS, Monte Carlo | code-reviewer, data-quality-analyst, data-contracts-engineer, test-generator, ai-data-engineer, ai-data-engineer-cloud, ai-data-engineer-gcp, gcp-data-architect, aws-data-architect, medallion-architect, lakeflow-expert, lakeflow-pipeline-builder, lakeflow-specialist, pipeline-architect |

### Infrastructure and Platforms

| Domain | Files | Description | Used By |
|--------|------:|-------------|---------|
| lakehouse | 10 | Iceberg v3, Delta Lake 4.1, DuckLake, Unity, Gravitino | lakehouse-architect, data-platform-engineer, lakeflow-architect, lakeflow-expert, lakeflow-pipeline-builder, lakeflow-specialist, spark-streaming-architect, spark-performance-analyzer |
| medallion | 10 | Bronze/Silver/Gold layer design, quality progression | medallion-architect, lakeflow-architect, lakeflow-expert, lakeflow-pipeline-builder |
| cloud-platforms | 10 | Snowflake Cortex, Databricks LakeFlow, BigQuery AI | data-platform-engineer, ai-data-engineer-cloud, ai-data-engineer-gcp, gcp-data-architect, spark-specialist, spark-performance-analyzer |
| aws | 20 | Lambda, S3, Glue, SAM deployment, IAM, Layers | aws-deployer, aws-lambda-architect, aws-data-architect, lambda-builder, ci-cd-specialist, ai-data-engineer-cloud |
| gcp | 13 | Cloud Run, Pub/Sub, GCS, BigQuery, IAM, Secret Manager | ai-data-engineer-gcp, ai-prompt-specialist-gcp, gcp-data-architect, ai-data-engineer-cloud |
| microsoft-fabric | 53 | Lakehouse, Warehouse, Pipelines, KQL, CI/CD, AI, Security | fabric-architect, fabric-pipeline-developer, fabric-logging-specialist, fabric-cicd-specialist, fabric-security-specialist, fabric-ai-specialist |
| lakeflow | 23 | DLT pipelines, materialized views, streaming tables, DABs | lakeflow-architect, lakeflow-expert, lakeflow-pipeline-builder, lakeflow-specialist, ci-cd-specialist |
| terraform | 14 | Resources, modules, providers, state, GCP/AWS patterns | aws-deployer, aws-lambda-architect, aws-data-architect, ai-data-engineer-cloud, ai-data-engineer-gcp, gcp-data-architect, ci-cd-specialist |

### AI and Modern

| Domain | Files | Description | Used By |
|--------|------:|-------------|---------|
| genai | 11 | Multi-agent systems, RAG, state machines, tool calling, guardrails | genai-architect, ai-prompt-specialist, llm-specialist, ai-prompt-specialist-gcp, qdrant-specialist |
| prompt-engineering | 11 | Chain-of-thought, structured extraction, few-shot, system prompts | ai-prompt-specialist, llm-specialist, ai-prompt-specialist-gcp, genai-architect |
| ai-data-engineering | 12 | RAG pipelines, vector DBs, feature stores, LLMOps, embeddings | ai-data-engineer, supabase-specialist, qdrant-specialist, genai-architect |
| modern-stack | 10 | DuckDB, Polars, SQLMesh, Malloy, local-first analytics | (general use) |

### Development Foundations

| Domain | Files | Description | Used By |
|--------|------:|-------------|---------|
| python | 10 | Dataclasses, type hints, generators, context managers | python-developer, code-cleaner, code-documenter |
| pydantic | 10 | BaseModel, validators, LLM output validation, extraction schemas | python-developer, ai-prompt-specialist, llm-specialist, ai-prompt-specialist-gcp |
| testing | 10 | pytest, fixtures, mocking, parametrize, Spark testing | python-developer, test-generator |

---

## How KB Integrates with Agents

Each agent declares a `kb_domains` field in its frontmatter that determines which domains it reads during KB-First Resolution.

### Agent-to-KB Mapping (by agent group)

**Architect agents** (8 agents in `.claude/agents/architect/`):

| Agent | KB Domains |
|-------|------------|
| data-platform-engineer | cloud-platforms, lakehouse, data-modeling |
| genai-architect | genai, prompt-engineering, ai-data-engineering |
| kb-architect | (none -- operates on KB structure itself) |
| lakehouse-architect | lakehouse, spark, data-modeling |
| medallion-architect | medallion, data-modeling, lakehouse, data-quality |
| pipeline-architect | airflow, data-quality, dbt |
| schema-designer | data-modeling, sql-patterns, data-quality |
| the-planner | (none -- strategic planning) |

**Cloud agents** (10 agents in `.claude/agents/cloud/`):

| Agent | KB Domains |
|-------|------------|
| ai-data-engineer-cloud | gcp, aws, terraform, data-quality, cloud-platforms |
| ai-data-engineer-gcp | gcp, terraform, cloud-platforms, data-quality |
| ai-prompt-specialist-gcp | prompt-engineering, genai, pydantic, gcp |
| aws-data-architect | aws, terraform, data-quality |
| aws-deployer | aws, terraform |
| aws-lambda-architect | aws, terraform |
| ci-cd-specialist | terraform, aws, lakeflow |
| gcp-data-architect | gcp, terraform, cloud-platforms, data-quality |
| lambda-builder | aws, python, testing |
| supabase-specialist | ai-data-engineering, data-modeling |

**Platform agents** (6 agents in `.claude/agents/platform/`):

| Agent | KB Domains |
|-------|------------|
| fabric-ai-specialist | microsoft-fabric |
| fabric-architect | microsoft-fabric |
| fabric-cicd-specialist | microsoft-fabric |
| fabric-logging-specialist | microsoft-fabric |
| fabric-pipeline-developer | microsoft-fabric |
| fabric-security-specialist | microsoft-fabric |

**Data engineering agents** (15 agents in `.claude/agents/data-engineering/`):

| Agent | KB Domains |
|-------|------------|
| ai-data-engineer | ai-data-engineering, data-quality, streaming |
| airflow-specialist | airflow, sql-patterns, data-quality |
| dbt-specialist | dbt, data-quality, sql-patterns |
| lakeflow-architect | lakeflow, lakehouse, spark, medallion |
| lakeflow-expert | lakeflow, lakehouse, data-quality, medallion |
| lakeflow-pipeline-builder | lakeflow, lakehouse, data-quality, medallion |
| lakeflow-specialist | lakeflow, lakehouse, spark, data-quality |
| qdrant-specialist | ai-data-engineering, genai |
| spark-engineer | spark, sql-patterns, streaming |
| spark-performance-analyzer | spark, cloud-platforms, lakehouse |
| spark-specialist | spark, sql-patterns, cloud-platforms |
| spark-streaming-architect | spark, streaming, lakehouse |
| spark-troubleshooter | spark, sql-patterns |
| sql-optimizer | sql-patterns, data-modeling, dbt |
| streaming-engineer | streaming, spark, sql-patterns |

**Python agents** (6 agents in `.claude/agents/python/`):

| Agent | KB Domains |
|-------|------------|
| ai-prompt-specialist | prompt-engineering, pydantic, genai |
| code-cleaner | python |
| code-documenter | python |
| code-reviewer | data-quality, sql-patterns, dbt |
| llm-specialist | prompt-engineering, pydantic, genai |
| python-developer | python, pydantic, testing |

**Test agents** (3 agents in `.claude/agents/test/`):

| Agent | KB Domains |
|-------|------------|
| data-contracts-engineer | data-quality, data-modeling |
| data-quality-analyst | data-quality, dbt, data-modeling |
| test-generator | data-quality, dbt, testing |

**Dev and Workflow agents** (10 agents) do not use KB domains directly.

---

## How KB Integrates with SDD Workflow

The SDD workflow references KB domains at every phase:

```text
DEFINE                     DESIGN                     BUILD
------                     ------                     -----

KB domains specified   ->  Agents pull patterns   ->  Agents consult KB
in requirements            from matched domains       during implementation

Example:                   Example:                   Example:
kb_domains:                spark-engineer reads        Reads patterns/
  - spark                  spark/index.md              delta-integration.md
  - lakehouse              for relevant concepts       for working code
```

---

## File Size Limits

Defined in `_index.yaml` and enforced across all domains:

| File Type | Max Lines | Purpose |
|-----------|----------:|---------|
| quick-reference | ~100 | Fast lookup tables, cheat sheets |
| concept | ~150 | Core concept explanation with examples |
| pattern | ~200 | Implementation pattern with production code |
| spec | no limit | Machine-readable specifications |
| reference | no limit | Detailed reference documentation |

---

## Creating a KB Domain

### Option 1: Use the slash command

```bash
/create-kb {domain-name}
```

This scaffolds the full domain structure, copies templates, and registers the domain in `_index.yaml`.

### Option 2: Manual creation

1. Create the directory structure:

```bash
mkdir -p .claude/kb/{domain}/{concepts,patterns}
```

2. Copy templates from `_templates/`:

```bash
cp .claude/kb/_templates/index.md.template .claude/kb/{domain}/index.md
cp .claude/kb/_templates/quick-reference.md.template .claude/kb/{domain}/quick-reference.md
cp .claude/kb/_templates/concept.md.template .claude/kb/{domain}/concepts/{name}.md
cp .claude/kb/_templates/pattern.md.template .claude/kb/{domain}/patterns/{name}.md
```

3. Fill in domain-specific content with working code examples.

4. Register the domain in `_index.yaml` under the `domains:` key.

5. Add the domain to relevant agents' `kb_domains` frontmatter.

---

## Best Practices

1. **Be specific** -- Reference actual code from real projects, not hypothetical examples
2. **Include examples** -- Working code snippets that can be copied and adapted
3. **Keep updated** -- Mark freshness dates; validate with MCP tools when updating
4. **Cite sources** -- Link to official documentation for version-sensitive content
5. **Stay within limits** -- Respect the line limits defined in `_index.yaml`
6. **One concept per file** -- Each file should cover exactly one idea
7. **Cross-reference** -- Link to related concepts and patterns in other domains
8. **Test examples** -- Every code block should be syntactically valid

---

## Registry Reference

The machine-readable registry lives at `.claude/kb/_index.yaml`. It defines:

- **version** -- Schema version of the index format
- **limits** -- File size limits (single source of truth)
- **templates** -- Paths to scaffolding templates
- **shared** -- Cross-domain resources (anti-patterns library)
- **domains** -- Complete registry of all 24 domains with:
  - `name` -- Domain identifier
  - `description` -- One-line summary
  - `path` -- Directory path relative to `.claude/kb/`
  - `mcp_validated` -- Date of last MCP validation
  - `entry_points` -- Primary files for agent resolution (`index`, `quick_reference`)
  - `concepts` -- List of concept files with confidence scores
  - `patterns` -- List of pattern files with confidence scores
  - `reference` -- (optional) List of reference files with no line limit

Agents resolve KB content by reading `_index.yaml` to discover available domains and their entry points, then loading specific files on demand based on the task at hand.
