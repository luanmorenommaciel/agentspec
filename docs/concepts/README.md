# Core Concepts

Understanding the mental model behind Spec-Driven Development for Data Engineering.

## The Component Model

AgentSpec separates its building blocks by responsibility: **agents** execute (identity, tool scope, escalation — thin shells), **skills** teach how (methodology and specialized knowledge), **commands** are entrypoints (argument surface, mode selection, sequencing), and **KBs** are source-of-truth deep dives. New logic goes to the layer that owns it. The canonical definition lives in the shared KB (`kb/shared/component-model.md`); the SDD workflow components — thin phase agents plus `sdd-*` skills plus thin phase commands — are the reference implementation.

## The Problem

Data engineering with AI assistants without structure leads to:

- **Lost decisions** — pipeline requirements discussed but never captured
- **Spec drift** — implementation diverges from data contracts
- **Repeated mistakes** — no institutional memory about partition strategies or SCD choices
- **No audit trail** — can't trace why a schema was modeled a certain way
- **Inconsistent quality** — hallucinated SQL, missing tests, wrong freshness SLAs

## The SDD Mental Model

AgentSpec solves this with a **5-phase pipeline** where each phase produces a traceable artifact:

```text
  Idea                                                    Shipped Pipeline
   │                                                            ▲
   ▼                                                            │
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────┐   ┌──────────┐
│BRAINSTORM│──▶│  DEFINE  │──▶│  DESIGN  │──▶│BUILD │──▶│   SHIP   │
│ explore  │   │ contract │   │ pipeline │   │execute│   │ archive  │
└──────────┘   └──────────┘   └──────────┘   └──────┘   └──────────┘
  Data Flow     Schema SLAs    DAG + Parts   dbt build    Lessons
  Sketch        Freshness      Incremental   sqlfluff     Learned
```

**Each arrow is a quality gate.** You can't proceed without meeting measurable criteria.

## The Three Pillars

### 1. Phases (the workflow)

Five phases that structure how data pipelines move from idea to production:

| Phase | What Happens | Quality Gate |
|-------|-------------|-------------|
| **Brainstorm** | Explore approaches, data flow sketches, volume estimates | Min 3 questions, 2+ approaches |
| **Define** | Capture requirements + data contracts, SLAs, source inventory | Clarity Score >= 12/15 |
| **Design** | Pipeline architecture, DAG, partitions, incremental strategy | Complete manifest, ADRs, schema plan |
| **Build** | Execute with dbt build, sqlfluff lint, GE suites | All tests + quality gates pass |
| **Ship** | Archive with lessons learned | Acceptance tests verified |

Brainstorm is optional. You can start directly with `/define` if requirements are clear.

### 2. Agents (the specialists)

58 specialized agents, each with a specific domain:

| Category | Count | Key Purpose |
|----------|-------|-------------|
| **Workflow** | 6 | SDD phase execution |
| **Architect** | 8 | System-level design (schema, pipeline, lakehouse, medallion, genai, planning) |
| **Cloud** | 10 | AWS, GCP, CI/CD, deployment |
| **Platform** | 6 | Microsoft Fabric specialists |
| **Python** | 6 | Code quality, prompts, documentation |
| **Test** | 3 | Testing, data quality, data contracts |
| **Data Engineering** | 15 | dbt, Spark, Airflow, Flink, Lakeflow, SQL, streaming |
| **Dev** | 4 | Developer productivity (codebase explorer, prompt crafter, shell scripts) |

During `/build`, the build-agent delegates to DE specialists: dbt models go to `dbt-specialist`, Spark jobs to `spark-engineer`, quality checks to `data-quality-analyst`, pipeline DAGs to `airflow-specialist`, and streaming workloads to `spark-streaming-architect`.

### 3. Knowledge Base (the memory)

24 KB domains ground agent responses in verified patterns instead of hallucinated SQL:

| Domain | Topics |
|--------|--------|
| `dbt` | Models, macros, incremental, testing |
| `spark` | PySpark, Spark SQL, performance tuning |
| `sql-patterns` | Window functions, CTEs, anti-patterns |
| `airflow` | DAGs, operators, sensors, dynamic mapping |
| `streaming` | Flink, Kafka, Spark Streaming, CDC |
| `data-modeling` | Star schema, Data Vault, SCD, normalization |
| `data-quality` | Great Expectations, Soda, data contracts |
| `lakehouse` | Iceberg, Delta Lake, catalogs |
| `cloud-platforms` | Snowflake, Databricks, BigQuery |
| `ai-data-engineering` | RAG, vector DBs, feature stores, LLMOps |
| `modern-stack` | DuckDB, Polars, SQLMesh, local-first analytics |
| `aws` | Lambda, S3, Glue, SAM, serverless patterns |
| `gcp` | Cloud Run, Pub/Sub, BigQuery, Dataflow |
| `microsoft-fabric` | Lakehouse, Warehouse, Pipelines, CI/CD |
| `lakeflow` | Databricks Lakeflow (DLT), serverless pipelines |
| `medallion` | Bronze/Silver/Gold architecture, layer transitions |
| `prompt-engineering` | Chain-of-thought, few-shot, structured extraction |
| `genai` | Multi-agent systems, RAG architecture, guardrails |
| `pydantic` | Validation, LLM output schemas, base models |
| `python` | Clean architecture, type hints, dataclasses |
| `testing` | pytest, fixtures, integration tests, CI |
| `terraform` | Modules, state, workspaces, IaC patterns |
| `supabase` | pgvector, RLS, Edge Functions, Auth, Realtime |
| `shared` | Cross-domain anti-patterns and conventions |

Create additional domains with `/create-kb <domain>` and agents will consult them during `/design` and `/build`.

## How Phases Connect

Context flows forward through the pipeline:

1. **BRAINSTORM** explores approaches, captures data flow sketches and volume estimates
2. **DEFINE** formalizes those into scored requirements with data contracts and SLAs
3. **DESIGN** reads DEFINE, creates pipeline architecture + DAG + partition strategy + agent assignments
4. **BUILD** reads DESIGN, delegates to DE agents, verifies with dbt build + sqlfluff + GE
5. **SHIP** reads BUILD_REPORT, archives everything with lessons learned

If requirements change mid-stream, use `/iterate` to update any phase document with automatic cascade detection.

## When to Use Each Phase

| Situation | Start With |
|-----------|-----------|
| Vague idea, need to explore data sources | `/brainstorm` |
| Clear pipeline requirements, ready to spec | `/define` |
| Quick schema design or quality check | `/schema`, `/data-quality` |
| Need a DAG scaffold quickly | `/pipeline` |
| Requirements changed after design | `/iterate` |
| Feature complete, ready to archive | `/ship` |

## Key Design Decisions

- **YAML contracts** enforce phase transitions (not human discipline)
- **Data contracts** in DEFINE prevent schema drift between producer and consumer
- **Pipeline architecture** in DESIGN captures DAGs, partitions, and incremental strategies
- **DE quality gates** in BUILD run dbt tests, sqlfluff, and GE suites
- **Agent matching** is automatic — dbt models go to dbt-specialist, Spark jobs to spark-engineer
- **KB domains** have line limits to stay focused and maintainable
- **Lessons learned** are structured, not freeform — they feed future decisions
