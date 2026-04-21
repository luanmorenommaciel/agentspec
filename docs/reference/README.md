# Reference

Complete catalog of commands, agents, KB domains, templates, and configuration.

## Slash Commands (31 total)

### Workflow Commands (7)

| Command | Purpose | Input | Output |
|---------|---------|-------|--------|
| `/brainstorm` | Explore ideas (Phase 0) | Idea description or file path | `BRAINSTORM_{FEATURE}.md` |
| `/define` | Capture requirements (Phase 1) | Brainstorm file, notes, or description | `DEFINE_{FEATURE}.md` |
| `/design` | Create architecture (Phase 2) | DEFINE file path | `DESIGN_{FEATURE}.md` |
| `/build` | Execute implementation (Phase 3) | DESIGN file path | `BUILD_REPORT_{FEATURE}.md` |
| `/ship` | Archive completed work (Phase 4) | DEFINE file path | `SHIPPED_{DATE}.md` |
| `/iterate` | Update any phase document | File path + change description | Updated document + cascades |
| `/create-pr` | Create pull request | Optional title, `--draft`, `--review` | GitHub PR |

### Data Engineering Commands (8)

| Command | Purpose | Primary Agent |
|---------|---------|---------------|
| `/pipeline` | DAG/pipeline scaffolding | pipeline-architect |
| `/schema` | Interactive schema design | schema-designer |
| `/data-quality` | Quality rules generation | data-quality-analyst |
| `/lakehouse` | Table format + catalog guidance | lakehouse-architect |
| `/sql-review` | SQL-specific code review | code-reviewer + sql-optimizer |
| `/ai-pipeline` | RAG/embedding scaffolding | ai-data-engineer |
| `/data-contract` | Contract authoring (ODCS) | data-contracts-engineer |
| `/migrate` | Legacy ETL migration | dbt-specialist + spark-engineer |

### Core Commands (4)

| Command | Purpose | Input |
|---------|---------|-------|
| `/meeting` | Meeting transcript analysis | Transcript text or file path |
| `/memory` | Save session insights to storage | Optional context note |
| `/sync-context` | Update CLAUDE.md from codebase | `--section`, `--dry-run` |
| `/readme-maker` | Generate README.md | `--output`, `--style` |

### Knowledge Commands (1)

| Command | Purpose | Input |
|---------|---------|-------|
| `/create-kb` | Create a KB domain | Domain name |

### Review Commands (1)

| Command | Purpose | Input |
|---------|---------|-------|
| `/review` | Dual AI code review | `uncommitted`, `committed`, `--base`, `--deep` |

### Visual Explainer Commands (8)

Generate self-contained HTML pages for visual documentation. Powered by the `visual-explainer` skill.

| Command | Purpose | Input |
|---------|---------|-------|
| `/generate-web-diagram` | Standalone HTML diagram | Topic or description |
| `/generate-slides` | Magazine-quality slide deck as HTML | Topic or description |
| `/generate-visual-plan` | Visual implementation plan with state machines | Feature description or spec |
| `/diff-review` | Before/after architecture comparison | Branch name or commit hash |
| `/plan-review` | Current codebase vs. proposed plan | Plan file path |
| `/project-recap` | Project state, decisions, cognitive debt | Time window (e.g., `2w`, `30d`) |
| `/fact-check` | Verify document accuracy against codebase | File path |
| `/share` | Share HTML page via Vercel | File path |

---

## Agents (58 total)

Agents are organized into 8 categories. Each agent declares a tier (T1/T2/T3) governing its template requirements, line budget, and response format.

| Tier | Name | Use For |
|------|------|---------|
| T1 | Utility | Single-purpose tools, lightweight helpers (80-150 lines) |
| T2 | Domain Expert | Domain specialists with KB resolution and confidence scoring (150-350 lines) |
| T3 | Platform Specialist | MCP-dependent agents with live platform access (350-600 lines) |

### Workflow Agents (6)

Drive the SDD workflow phases.

| Agent | Tier | Model | Phase | Purpose |
|-------|------|-------|-------|---------|
| `brainstorm-agent` | T2 | Sonnet | 0 | Explore ideas through collaborative dialogue |
| `define-agent` | T2 | Sonnet | 1 | Capture requirements with clarity scoring |
| `design-agent` | T2 | Opus | 2 | Create technical architecture with file manifest |
| `build-agent` | T2 | Opus | 3 | Execute implementation with agent delegation |
| `ship-agent` | T2 | Sonnet | 4 | Archive with lessons learned |
| `iterate-agent` | T2 | Sonnet | All | Update documents with cascade awareness |

### Architect Agents (8)

System-level design and architecture decisions.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `genai-architect` | T1 | Opus | Multi-agent orchestration, agentic workflows, production AI systems |
| `the-planner` | T2 | Opus | Strategic architecture and comprehensive implementation plans |
| `kb-architect` | T2 | Sonnet | Knowledge base domain creation and audit |
| `lakehouse-architect` | T2 | Sonnet | Iceberg, Delta Lake, catalog governance design |
| `medallion-architect` | T1 | Sonnet | Bronze/Silver/Gold layer design, data quality progression |
| `pipeline-architect` | T2 | Sonnet | Airflow, Dagster, DAG design patterns |
| `schema-designer` | T2 | Sonnet | Dimensional modeling, SCD, Data Vault |
| `data-platform-engineer` | T2 | Sonnet | Snowflake, Databricks, BigQuery, cost optimization |

### Cloud Agents (10)

Cloud provider services, deployment, and CI/CD.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `aws-data-architect` | T1 | Sonnet | Lambda, S3, Glue, Redshift, MWAA, serverless pipelines |
| `aws-deployer` | T3 | Sonnet | SAM, CloudFormation, CI/CD, Terraform for AWS |
| `aws-lambda-architect` | T3 | Sonnet | SAM templates, least-privilege IAM policies |
| `lambda-builder` | T3 | Sonnet | Python Lambda handlers, S3-triggered functions |
| `gcp-data-architect` | T1 | Sonnet | BigQuery, Cloud Run, Pub/Sub, Dataflow, Vertex AI |
| `ai-data-engineer-gcp` | T2 | Sonnet | GCP serverless architectures, Cloud Functions, BigQuery pipelines |
| `ai-data-engineer-cloud` | T3 | Sonnet | Cloud architecture optimization, AI/ML pipelines |
| `ai-prompt-specialist-gcp` | T3 | Sonnet | Google Gemini, Vertex AI, multi-modal document extraction |
| `ci-cd-specialist` | T3 | Sonnet | Azure DevOps, Terraform, Databricks Asset Bundles |
| `supabase-specialist` | T3 | Opus | pgvector, RLS, Edge Functions, Auth, Realtime |

### Platform Agents (6)

Microsoft Fabric specialists.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `fabric-architect` | T3 | Opus | End-to-end Fabric architecture, OneLake, workload selection |
| `fabric-pipeline-developer` | T3 | Sonnet | Data Factory pipelines, PySpark notebooks, Dataflow Gen2 |
| `fabric-ai-specialist` | T3 | Sonnet | Fabric Copilot, ML models, AI Skills, Azure OpenAI |
| `fabric-cicd-specialist` | T3 | Sonnet | Fabric CI/CD, Git integration, deployment pipelines |
| `fabric-logging-specialist` | T3 | Sonnet | Workspace monitoring, KQL queries, dashboards |
| `fabric-security-specialist` | T3 | Opus | RLS, permissions, data masking, encryption, compliance |

### Python Agents (6)

Python development, code quality, and prompt engineering.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `python-developer` | T1 | Sonnet | Python code architecture, dataclasses, type hints |
| `code-reviewer` | T2 | Sonnet | Review code for quality and security issues |
| `code-cleaner` | T2 | Sonnet | Clean code, remove redundant comments, apply DRY |
| `code-documenter` | T2 | Sonnet | Generate documentation, READMEs, API docs |
| `ai-prompt-specialist` | T1 | Sonnet | Prompt optimization, structured extraction, few-shot |
| `llm-specialist` | T3 | Opus | Advanced prompt engineering, chain-of-thought, structured output |

### Test Agents (3)

Testing, data quality, and contract validation.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `test-generator` | T2 | Sonnet | Generate pytest tests with fixtures |
| `data-quality-analyst` | T2 | Sonnet | Great Expectations, dbt tests, data contracts |
| `data-contracts-engineer` | T2 | Sonnet | ODCS, SLAs, schema governance |

### Data Engineering Agents (15)

Implementation specialists for data pipelines and processing.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `dbt-specialist` | T2 | Sonnet | dbt models, macros, tests, incremental strategies |
| `spark-engineer` | T2 | Sonnet | PySpark, Spark SQL, distributed processing |
| `spark-specialist` | T2 | Opus | Spark architecture, configuration, performance |
| `spark-troubleshooter` | T1 | Sonnet | Spark debugging — OOM, data skew, shuffle failures |
| `spark-performance-analyzer` | T1 | Sonnet | Spark tuning — memory, partitions, joins, AQE |
| `spark-streaming-architect` | T3 | Sonnet | Structured Streaming, Kafka, real-time pipelines |
| `streaming-engineer` | T2 | Sonnet | Flink, Kafka, Spark Streaming, CDC |
| `sql-optimizer` | T2 | Sonnet | Query plans, cross-dialect SQL, window functions |
| `airflow-specialist` | T3 | Sonnet | Apache Airflow 3.0, DAGs, TaskFlow API |
| `lakeflow-architect` | T3 | Sonnet | Databricks Lakeflow, Medallion architecture |
| `lakeflow-expert` | T3 | Sonnet | DLT troubleshooting, CDC, SCD Type 2 |
| `lakeflow-pipeline-builder` | T3 | Sonnet | DLT pipeline creation, quality expectations |
| `lakeflow-specialist` | T1 | Sonnet | Declarative pipelines, materialized views, streaming tables |
| `ai-data-engineer` | T2 | Sonnet | RAG pipelines, vector DBs, feature stores |
| `qdrant-specialist` | T3 | Opus | Qdrant vector database, collection management |

### Dev Agents (4)

Developer tools and productivity.

| Agent | Tier | Model | Purpose |
|-------|------|-------|---------|
| `prompt-crafter` | T1 | Sonnet | SDD-lite PROMPT.md builder with agent matching |
| `codebase-explorer` | T2 | Sonnet | Analyze codebase structure with health scoring |
| `meeting-analyst` | T2 | Sonnet | Extract decisions and action items from meetings |
| `shell-script-specialist` | T2 | Sonnet | Production-grade Bash scripts, automation, deployment scripts |

---

## Knowledge Base Domains (22 total)

Domains are grouped into five areas. Each domain contains an `index.md`, a `quick-reference.md`, and `concepts/` and `patterns/` subdirectories.

### Core Data Engineering (5)

| Domain | Description | Key Topics |
|--------|-------------|------------|
| `dbt` | dbt development patterns — Fusion Engine, Mesh, Semantic Layer | Models, macros, incremental strategies, testing, semantic layer |
| `spark` | PySpark and Spark SQL patterns | DataFrames, partitioning, Catalyst optimizer, Delta integration |
| `airflow` | Orchestration patterns — Airflow 3.x, Dagster, Prefect | DAG design, TaskFlow API, sensors, dynamic task mapping |
| `sql-patterns` | Cross-dialect SQL — DuckDB, Snowflake, BigQuery, Spark | Window functions, CTEs, deduplication, pivot/unpivot |
| `streaming` | Stream processing — Flink, Kafka, Spark Streaming, CDC | Flink SQL, Kafka producer/consumer, streaming databases |

### Data Design and Quality (3)

| Domain | Description | Key Topics |
|--------|-------------|------------|
| `data-modeling` | Schema design — dimensional modeling, Data Vault, SCD types | Star schema, Data Vault 2.0, SCD Type 2, schema evolution |
| `data-quality` | Data quality, contracts, and observability | Great Expectations, Soda Core, dbt tests, ODCS, Monte Carlo |
| `medallion` | Medallion Architecture — Bronze/Silver/Gold layer design | Layer transitions, data quality gates, incremental loading |

### Infrastructure and Platforms (4)

| Domain | Description | Key Topics |
|--------|-------------|------------|
| `lakehouse` | Open table formats and catalogs — Iceberg v3, Delta Lake | Iceberg v3, Delta Lake 4.1, DuckLake, Unity Catalog, Gravitino |
| `cloud-platforms` | Cloud data platforms — Snowflake, Databricks, BigQuery | Snowflake Cortex, Databricks Lakeflow, BigQuery AI, cost optimization |
| `lakeflow` | Databricks Lakeflow — DLT pipelines and expectations | Materialized views, streaming tables, CDC, DABs deployment |
| `microsoft-fabric` | Microsoft Fabric — end-to-end platform | Lakehouse, Warehouse, Pipelines, Real-Time Analytics, KQL, CI/CD, AI |

### Cloud Provider Deep Dives (3)

| Domain | Description | Key Topics |
|--------|-------------|------------|
| `aws` | AWS data engineering — Lambda, S3, Glue, MWAA | SAM templates, IAM policies, S3 triggers, Powertools logging |
| `gcp` | Google Cloud Platform — Cloud Run, Pub/Sub, BigQuery | Cloud Run scaling, event-driven pipelines, GCS-triggered workflows |
| `terraform` | Terraform IaC — resources, modules, state | GCP/AWS modules, remote state, workspaces, provider config |

### AI and Prompt Engineering (7)

| Domain | Description | Key Topics |
|--------|-------------|------------|
| `ai-data-engineering` | AI data engineering — RAG, vector DBs, feature stores | Embedding pipelines, LLMOps, text-to-SQL, training data |
| `modern-stack` | Modern data tools — DuckDB, Polars, SQLMesh | Local-first analytics, analytical query patterns |
| `prompt-engineering` | Prompt engineering — chain-of-thought, extraction | Few-shot prompting, structured extraction, system prompts |
| `genai` | GenAI architecture — multi-agent systems, RAG | State machines, tool calling, guardrails, evaluation |
| `pydantic` | Pydantic patterns — BaseModel, validators | LLM output validation, extraction schemas, error handling |
| `python` | Python patterns — dataclasses, type hints | Clean architecture, generators, context managers |
| `testing` | Testing patterns — pytest, fixtures, mocking | Unit tests, fixture factories, integration tests, Spark testing |

---

## SDD Templates

All templates live in `.claude/sdd/templates/`:

| Template | Phase | Purpose | DE Sections |
|----------|-------|---------|-------------|
| `BRAINSTORM_TEMPLATE.md` | Phase 0 | Idea exploration | Data Engineering Context (sources, volumes, flow) |
| `DEFINE_TEMPLATE.md` | Phase 1 | Requirements with clarity score | Data Contract (schema, SLAs, lineage) |
| `DESIGN_TEMPLATE.md` | Phase 2 | Architecture with file manifest | Pipeline Architecture (DAG, partitions, incremental, quality gates) |
| `BUILD_REPORT_TEMPLATE.md` | Phase 3 | Execution report with agent attribution | Data Quality Results (dbt build, sqlfluff, GE, freshness) |
| `SHIPPED_TEMPLATE.md` | Phase 4 | Archive with lessons learned | — |

---

## KB Templates

All templates live in `.claude/kb/_templates/`:

| Template | Purpose |
|----------|---------|
| `index.md.template` | Domain overview and navigation |
| `quick-reference.md.template` | Cheat sheet (max 100 lines) |
| `concept.md.template` | Core concept explanation (max 150) |
| `pattern.md.template` | Implementation pattern (max 200) |
| `domain-manifest.yaml.template` | Domain metadata and file registry |
| `spec.yaml.template` | Machine-readable specifications |
| `test-case.json.template` | Validation test cases |

---

## Skills (2 core + 2 plugin-only)

Skills are reusable capability packs in `.claude/skills/` that provide templates, references, and scripts for specialized generation tasks.

| Skill | Description | Commands |
|-------|-------------|----------|
| `visual-explainer` | Self-contained HTML pages for diagrams, slides, reviews, and recaps | 8 visual-explainer commands |
| `excalidraw-diagram` | Excalidraw JSON files for workflow and architecture visualization | Invoked directly |

### Plugin-Only Skills

These skills are bundled in the distributed plugin (`plugin/skills/`) but are not part of the `.claude/` source tree. They are merged in by `build-plugin.sh`.

| Skill | Description |
|-------|-------------|
| `sdd-workflow` | Spec-Driven Development workflow guidance for structured feature development. Proactively guides through the 5-phase SDD workflow: Brainstorm → Define → Design → Build → Ship. |
| `data-engineering-guide` | Data engineering expertise for pipelines, schemas, data quality, SQL, lakehouse, and streaming. Routes users to the right command and agent based on their task, backed by 23 KB domains. |

---

## Configuration

### Workflow Contracts

Phase transition rules are defined in `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`:

- Phase inputs, outputs, and quality gates
- Model allocation per phase (Opus/Sonnet/Haiku)
- Naming conventions (`SCREAMING_SNAKE_CASE`)
- Cascade rules for `/iterate`
- Status transition logic
- Data engineering delegation map and quality gates
- Data anti-patterns checklist

### Settings

Project settings in `.claude/settings.local.json` (auto-generated, gitignored — personal to each developer):

- `permissions` — tool access control
- `outputStyle` — response formatting (e.g., "Explanatory")

---

## File Naming Conventions

| Artifact | Pattern | Location |
|----------|---------|----------|
| Brainstorm document | `BRAINSTORM_{FEATURE}.md` | `.claude/sdd/features/` |
| Requirements document | `DEFINE_{FEATURE}.md` | `.claude/sdd/features/` |
| Design document | `DESIGN_{FEATURE}.md` | `.claude/sdd/features/` |
| Build report | `BUILD_REPORT_{FEATURE}.md` | `.claude/sdd/reports/` |
| Shipped archive | `SHIPPED_{YYYY-MM-DD}.md` | `.claude/sdd/archive/{FEATURE}/` |

Feature names use `SCREAMING_SNAKE_CASE` (e.g., `ORDERS_PIPELINE`, `STAR_SCHEMA`).
