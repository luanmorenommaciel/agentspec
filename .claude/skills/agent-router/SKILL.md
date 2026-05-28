---
name: agent-router
description: Intelligent agent routing -- automatically matches tasks to the best specialist agent based on file patterns, intent keywords, and domain context. Loaded every session to give Claude explicit routing rules for all 58 AgentSpec agents.
---

<!-- =========================================================================
     GENERATED FILE — DO NOT EDIT BY HAND
     Source of truth: .claude/agents/**/*.md frontmatter
     Regenerate:      python3 scripts/generate-agent-router.py
     CI check:        python3 scripts/generate-agent-router.py --check
     ========================================================================= -->

# Agent Router

Explicit routing rules for matching tasks to the correct specialist agent. Generated from each agent's frontmatter, so any change to an agent's `description`, `kb_domains`, or `escalation_rules` flows here automatically.

**Agent count:** 58  |  **Categories:** 8  |  **Content hash:** `d2970b1b988f`

## A. Agents by Category

### Architecture & Design
*System-level design, schemas, pipelines, lakehouse*

| Agent | Tier | Model | KB Domains | Escalates To |
|-------|------|-------|-----------|--------------|
| `data-platform-engineer` | T2 | sonnet | `cloud-platforms`, `lakehouse`, `data-modeling` | `lakehouse-architect`, `pipeline-architect`, `schema-designer` |
| `genai-architect` | T1 | opus | `genai`, `prompt-engineering`, `ai-data-engineering` | — |
| `kb-architect` | T2 | sonnet | — | `user` |
| `lakehouse-architect` | T2 | sonnet | `lakehouse`, `spark`, `data-modeling` | `data-platform-engineer`, `spark-engineer`, `schema-designer` |
| `medallion-architect` | T1 | sonnet | `medallion`, `data-modeling`, `lakehouse`, `data-quality` | — |
| `pipeline-architect` | T2 | sonnet | `airflow`, `data-quality`, `dbt` | `dbt-specialist`, `spark-engineer`, `streaming-engineer` |
| `schema-designer` | T2 | sonnet | `data-modeling`, `sql-patterns`, `data-quality` | `dbt-specialist`, `lakehouse-architect`, `data-quality-analyst`, `sql-optimizer` |
| `the-planner` | T2 | opus | — | `user` |

### Cloud & Infrastructure
*AWS, GCP, CI/CD, deployment*

| Agent | Tier | Model | KB Domains | Escalates To |
|-------|------|-------|-----------|--------------|
| `ai-data-engineer-cloud` | T3 | sonnet | `gcp`, `aws`, `terraform`, `data-quality`, `cloud-platforms` | `ai-data-engineer-gcp`, `aws-data-architect`, `user` |
| `ai-data-engineer-gcp` | T2 | sonnet | `gcp`, `terraform`, `cloud-platforms`, `data-quality` | `aws-data-architect`, `user` |
| `ai-prompt-specialist-gcp` | T3 | sonnet | `prompt-engineering`, `genai`, `pydantic`, `gcp` | `gcp-data-architect`, `user` |
| `aws-data-architect` | T1 | sonnet | `aws`, `terraform`, `data-quality` | — |
| `aws-deployer` | T3 | sonnet | `aws`, `terraform` | `aws-lambda-architect`, `ci-cd-specialist`, `user` |
| `aws-lambda-architect` | T3 | sonnet | `aws`, `terraform` | `aws-deployer`, `lambda-builder`, `user` |
| `ci-cd-specialist` | T3 | sonnet | `terraform`, `aws`, `lakeflow` | `lambda-builder`, `aws-lambda-architect`, `user` |
| `gcp-data-architect` | T1 | sonnet | `gcp`, `terraform`, `cloud-platforms`, `data-quality` | — |
| `lambda-builder` | T3 | sonnet | `aws`, `python`, `testing` | `aws-lambda-architect`, `aws-deployer`, `user` |
| `supabase-specialist` | T3 | opus | `supabase`, `ai-data-engineering`, `data-modeling` | `gcp-data-architect`, `aws-data-architect`, `user` |

### Data Engineering
*dbt, Spark, SQL, Airflow, streaming, data quality*

| Agent | Tier | Model | KB Domains | Escalates To |
|-------|------|-------|-----------|--------------|
| `ai-data-engineer` | T2 | sonnet | `ai-data-engineering`, `data-quality`, `streaming` | `pipeline-architect`, `spark-engineer`, `streaming-engineer`, `data-quality-analyst` |
| `airflow-specialist` | T3 | sonnet | `airflow`, `sql-patterns`, `data-quality` | `spark-engineer`, `dbt-specialist`, `streaming-engineer` |
| `dbt-specialist` | T2 | sonnet | `dbt`, `data-quality`, `sql-patterns` | `schema-designer`, `spark-engineer`, `pipeline-architect`, `data-quality-analyst` |
| `lakeflow-architect` | T3 | sonnet | `lakeflow`, `lakehouse`, `spark`, `medallion` | `spark-engineer`, `dbt-specialist`, `airflow-specialist` |
| `lakeflow-expert` | T3 | sonnet | `lakeflow`, `lakehouse`, `data-quality`, `medallion` | `spark-engineer`, `airflow-specialist`, `schema-designer` |
| `lakeflow-pipeline-builder` | T3 | sonnet | `lakeflow`, `lakehouse`, `data-quality`, `medallion` | `spark-engineer`, `airflow-specialist`, `schema-designer` |
| `lakeflow-specialist` | T1 | sonnet | `lakeflow`, `lakehouse`, `spark`, `data-quality` | — |
| `qdrant-specialist` | T3 | opus | `ai-data-engineering`, `genai` | `ai-data-engineer`, `spark-engineer`, `ai-data-engineer` |
| `spark-engineer` | T2 | sonnet | `spark`, `sql-patterns`, `streaming` | `pipeline-architect`, `dbt-specialist`, `lakehouse-architect` |
| `spark-performance-analyzer` | T1 | sonnet | `spark`, `cloud-platforms`, `lakehouse` | — |
| `spark-specialist` | T2 | opus | `spark`, `sql-patterns`, `cloud-platforms` | `pipeline-architect`, `dbt-specialist`, `lakehouse-architect` |
| `spark-streaming-architect` | T3 | sonnet | `spark`, `streaming`, `lakehouse` | `spark-engineer`, `streaming-engineer`, `airflow-specialist` |
| `spark-troubleshooter` | T1 | sonnet | `spark`, `sql-patterns` | — |
| `sql-optimizer` | T2 | sonnet | `sql-patterns`, `data-modeling`, `dbt` | `spark-engineer`, `schema-designer`, `dbt-specialist` |
| `streaming-engineer` | T2 | sonnet | `streaming`, `spark`, `sql-patterns` | `pipeline-architect`, `dbt-specialist`, `lakehouse-architect`, `ai-data-engineer` |

### Developer Tools
*Codebase exploration, meeting analysis, shell, prompts*

| Agent | Tier | Model | KB Domains | Escalates To |
|-------|------|-------|-----------|--------------|
| `codebase-explorer` | T2 | sonnet | — | `python-developer`, `the-planner` |
| `meeting-analyst` | T2 | sonnet | — | `the-planner`, `pipeline-architect` |
| `prompt-crafter` | T1 | sonnet | `python` | — |
| `shell-script-specialist` | T2 | sonnet | — | `python-developer`, `ci-cd-specialist` |

### Microsoft Fabric
*Fabric lakehouse, pipelines, AI, security*

| Agent | Tier | Model | KB Domains | Escalates To |
|-------|------|-------|-----------|--------------|
| `fabric-ai-specialist` | T3 | sonnet | `microsoft-fabric` | `user`, `fabric-security-specialist` |
| `fabric-architect` | T3 | opus | `microsoft-fabric` | `user`, `fabric-security-specialist` |
| `fabric-cicd-specialist` | T3 | sonnet | `microsoft-fabric` | `user`, `fabric-security-specialist` |
| `fabric-logging-specialist` | T3 | sonnet | `microsoft-fabric` | `user`, `fabric-security-specialist` |
| `fabric-pipeline-developer` | T3 | sonnet | `microsoft-fabric` | `user`, `fabric-architect` |
| `fabric-security-specialist` | T3 | opus | `microsoft-fabric` | `user`, `user` |

### Python & Code Quality
*Python dev, review, cleanup, documentation, LLM prompts*

| Agent | Tier | Model | KB Domains | Escalates To |
|-------|------|-------|-----------|--------------|
| `ai-prompt-specialist` | T1 | sonnet | `prompt-engineering`, `pydantic`, `genai` | — |
| `code-cleaner` | T2 | sonnet | `python` | — |
| `code-documenter` | T2 | sonnet | `python` | — |
| `code-reviewer` | T2 | sonnet | `data-quality`, `sql-patterns`, `dbt` | — |
| `llm-specialist` | T3 | opus | `prompt-engineering`, `pydantic`, `genai` | — |
| `python-developer` | T1 | sonnet | `python`, `pydantic`, `testing` | — |

### Testing & Contracts
*pytest, data quality, ODCS contracts*

| Agent | Tier | Model | KB Domains | Escalates To |
|-------|------|-------|-----------|--------------|
| `data-contracts-engineer` | T2 | sonnet | `data-quality`, `data-modeling` | `data-quality-analyst`, `schema-designer`, `dbt-specialist` |
| `data-quality-analyst` | T2 | sonnet | `data-quality`, `dbt`, `data-modeling` | `dbt-specialist`, `schema-designer`, `data-contracts-engineer` |
| `test-generator` | T2 | sonnet | `data-quality`, `dbt`, `testing` | `schema-designer`, `dbt-specialist`, `data-quality-analyst` |

### SDD Workflow
*Brainstorm, Define, Design, Build, Ship, Iterate*

| Agent | Tier | Model | KB Domains | Escalates To |
|-------|------|-------|-----------|--------------|
| `brainstorm-agent` | T2 | sonnet | — | `define-agent` |
| `build-agent` | T2 | opus | — | `design-agent` |
| `define-agent` | T2 | sonnet | — | `design-agent` |
| `design-agent` | T2 | opus | — | `build-agent` |
| `iterate-agent` | T2 | sonnet | — | `define-agent`, `design-agent`, `build-agent` |
| `ship-agent` | T2 | sonnet | — | `build-agent` |

## B. KB Domain → Agents

Which agents know which domain. Use this when the user names a technology.

| KB Domain | Agents |
|-----------|--------|
| `ai-data-engineering` | `ai-data-engineer`, `genai-architect`, `qdrant-specialist`, `supabase-specialist` |
| `airflow` | `airflow-specialist`, `pipeline-architect` |
| `aws` | `ai-data-engineer-cloud`, `aws-data-architect`, `aws-deployer`, `aws-lambda-architect`, `ci-cd-specialist`, `lambda-builder` |
| `cloud-platforms` | `ai-data-engineer-cloud`, `ai-data-engineer-gcp`, `data-platform-engineer`, `gcp-data-architect`, `spark-performance-analyzer`, `spark-specialist` |
| `data-modeling` | `data-contracts-engineer`, `data-platform-engineer`, `data-quality-analyst`, `lakehouse-architect`, `medallion-architect`, `schema-designer`, `sql-optimizer`, `supabase-specialist` |
| `data-quality` | `ai-data-engineer`, `ai-data-engineer-cloud`, `ai-data-engineer-gcp`, `airflow-specialist`, `aws-data-architect`, `code-reviewer`, `data-contracts-engineer`, `data-quality-analyst`, `dbt-specialist`, `gcp-data-architect`, `lakeflow-expert`, `lakeflow-pipeline-builder`, `lakeflow-specialist`, `medallion-architect`, `pipeline-architect`, `schema-designer`, `test-generator` |
| `dbt` | `code-reviewer`, `data-quality-analyst`, `dbt-specialist`, `pipeline-architect`, `sql-optimizer`, `test-generator` |
| `gcp` | `ai-data-engineer-cloud`, `ai-data-engineer-gcp`, `ai-prompt-specialist-gcp`, `gcp-data-architect` |
| `genai` | `ai-prompt-specialist`, `ai-prompt-specialist-gcp`, `genai-architect`, `llm-specialist`, `qdrant-specialist` |
| `lakeflow` | `ci-cd-specialist`, `lakeflow-architect`, `lakeflow-expert`, `lakeflow-pipeline-builder`, `lakeflow-specialist` |
| `lakehouse` | `data-platform-engineer`, `lakeflow-architect`, `lakeflow-expert`, `lakeflow-pipeline-builder`, `lakeflow-specialist`, `lakehouse-architect`, `medallion-architect`, `spark-performance-analyzer`, `spark-streaming-architect` |
| `medallion` | `lakeflow-architect`, `lakeflow-expert`, `lakeflow-pipeline-builder`, `medallion-architect` |
| `microsoft-fabric` | `fabric-ai-specialist`, `fabric-architect`, `fabric-cicd-specialist`, `fabric-logging-specialist`, `fabric-pipeline-developer`, `fabric-security-specialist` |
| `prompt-engineering` | `ai-prompt-specialist`, `ai-prompt-specialist-gcp`, `genai-architect`, `llm-specialist` |
| `pydantic` | `ai-prompt-specialist`, `ai-prompt-specialist-gcp`, `llm-specialist`, `python-developer` |
| `python` | `code-cleaner`, `code-documenter`, `lambda-builder`, `prompt-crafter`, `python-developer` |
| `spark` | `lakeflow-architect`, `lakeflow-specialist`, `lakehouse-architect`, `spark-engineer`, `spark-performance-analyzer`, `spark-specialist`, `spark-streaming-architect`, `spark-troubleshooter`, `streaming-engineer` |
| `sql-patterns` | `airflow-specialist`, `code-reviewer`, `dbt-specialist`, `schema-designer`, `spark-engineer`, `spark-specialist`, `spark-troubleshooter`, `sql-optimizer`, `streaming-engineer` |
| `streaming` | `ai-data-engineer`, `spark-engineer`, `spark-streaming-architect`, `streaming-engineer` |
| `supabase` | `supabase-specialist` |
| `terraform` | `ai-data-engineer-cloud`, `ai-data-engineer-gcp`, `aws-data-architect`, `aws-deployer`, `aws-lambda-architect`, `ci-cd-specialist`, `gcp-data-architect` |
| `testing` | `lambda-builder`, `python-developer`, `test-generator` |
## C. Agent One-Liners

Single-sentence purpose per agent, derived from frontmatter `description`.

- **`ai-data-engineer`** — AI data engineering specialist for RAG pipelines, vector databases, feature stores, and LLMOps.
- **`ai-data-engineer-cloud`** — Expert Data Engineer for cloud architectures and AI pipelines. Uses KB + MCP validation for best practices.
- **`ai-data-engineer-gcp`** — Elite GCP Data Engineering architect for serverless architectures, AI/ML pipelines, and document processing.
- **`ai-prompt-specialist`** — Prompt engineering specialist for LLMs — extraction, structured output, chain-of-thought, few-shot.
- **`ai-prompt-specialist-gcp`** — Elite Prompt Engineering architect for Google Gemini, Vertex AI, and multi-modal document extraction systems. Masters structured extraction, OCR optimization, and production prompt pipelines. Uses KB + MCP validation.
- **`airflow-specialist`** — Apache Airflow 3.0 SME for DAG development, asset-aware scheduling, and event-driven pipelines.
- **`aws-data-architect`** — AWS data architecture specialist for Lambda, S3, Glue, Redshift, MWAA, and serverless data pipelines.
- **`aws-deployer`** — Executes AWS CLI and SAM CLI deployment commands with validation. Uses KB + MCP validation for safe deployments.
- **`aws-lambda-architect`** — Creates SAM templates with embedded least-privilege IAM policies. Uses KB + MCP validation for secure Lambda deployments.
- **`brainstorm-agent`** — Collaborative exploration specialist for clarifying intent and approach (Phase 0).
- **`build-agent`** — Implementation executor with agent delegation (Phase 3).
- **`ci-cd-specialist`** — DevOps expert for Azure DevOps, Terraform, and Databricks Asset Bundles. Builds CI/CD pipelines for Lambda and Lakeflow deployment with multi-environment promotion. Uses KB + MCP validation for production-ready automation.
- **`code-cleaner`** — Python code cleaning specialist for removing noise and applying modern patterns.
- **`code-documenter`** — Documentation specialist for creating comprehensive, production-ready documentation.
- **`code-reviewer`** — Expert code review specialist ensuring quality, security, and maintainability.
- **`codebase-explorer`** — Elite codebase analyst delivering Executive Summaries + Deep Dives.
- **`data-contracts-engineer`** — Data contract specialist for ODCS, SLA enforcement, schema governance, and producer-consumer agreements.
- **`data-platform-engineer`** — Cloud data platform specialist for Snowflake, Databricks, BigQuery, and infrastructure decisions.
- **`data-quality-analyst`** — Data quality specialist for Great Expectations, Soda, dbt tests, data contracts, and observability.
- **`dbt-specialist`** — dbt Core and dbt Cloud specialist for model development, testing, macros, and project management.
- **`define-agent`** — Requirements extraction and validation specialist (Phase 1).
- **`design-agent`** — Architecture and technical specification specialist (Phase 2).
- **`fabric-ai-specialist`** — Expert in Microsoft Fabric AI capabilities - Copilot, ML models, AI Skills, and Azure OpenAI integration.
- **`fabric-architect`** — Strategic Fabric solution architect for end-to-end architectures using KB + MCP validation.
- **`fabric-cicd-specialist`** — Expert in Microsoft Fabric CI/CD, Git integration, and deployment pipelines.
- **`fabric-logging-specialist`** — Expert in Microsoft Fabric logging, monitoring, KQL queries, and observability.
- **`fabric-pipeline-developer`** — Expert in Fabric Data Factory pipelines, orchestration, and ETL workflows.
- **`fabric-security-specialist`** — Expert in Microsoft Fabric security, governance, and compliance.
- **`gcp-data-architect`** — Google Cloud data architecture specialist for BigQuery, Cloud Run, Pub/Sub, GCS, Dataflow, and Vertex AI.
- **`genai-architect`** — GenAI Systems Architect for multi-agent orchestration, agentic workflows, and production AI systems.
- **`iterate-agent`** — Cross-phase document updater with cascade awareness (All Phases).
- **`kb-architect`** — Knowledge base architect for creating validated, structured KB domains.
- **`lakeflow-architect`** — Databricks Lakeflow expert for building Medallion architecture pipelines. Creates Bronze/Silver/Gold layers with DLT. Uses KB + MCP validation.
- **`lakeflow-expert`** — Databricks Lakeflow (DLT) SME for pipeline development, CDC, data quality, and production deployment. Uses KB + MCP validation.
- **`lakeflow-pipeline-builder`** — Builds Databricks Lakeflow (DLT) pipelines for Medallion Architecture. Uses KB + MCP validation for production-ready pipelines.
- **`lakeflow-specialist`** — Databricks Lakeflow (DLT) specialist for declarative pipelines, materialized views, streaming tables, and expectations.
- **`lakehouse-architect`** — Open table format and catalog specialist for Iceberg, Delta Lake, and lakehouse governance.
- **`lambda-builder`** — AWS Lambda expert for Python serverless file processing. Builds S3-triggered Lambda functions with proper error handling, structured logging, and Parquet output. Uses KB + MCP validation for production-ready code.
- **`llm-specialist`** — Prompt engineering specialist and LLM expert. Masters structured prompting, chain-of-thought reasoning, and AI-powered extraction. Uses KB + MCP validation for optimized, production-ready prompts.
- **`medallion-architect`** — Medallion Architecture specialist for Bronze/Silver/Gold layer design and data quality progression.
- **`meeting-analyst`** — Master communication analyst that transforms meetings into structured, actionable documentation.
- **`pipeline-architect`** — Orchestration specialist for Airflow, Dagster, and pipeline design patterns.
- **`prompt-crafter`** — PROMPT.md builder with SDD-lite phases and Agent Matching Engine.
- **`python-developer`** — Python code architect for data engineering systems — clean patterns, dataclasses, type hints, generators.
- **`qdrant-specialist`** — Elite Qdrant vector database specialist for collection management, point operations, payload filtering, search optimization, and RAG pipeline integration.
- **`schema-designer`** — Data modeling specialist for dimensional modeling, Data Vault, SCD types, and schema evolution.
- **`shell-script-specialist`** — Elite shell scripting specialist for building production-grade Bash scripts with best practices, error handling, and cross-platform compatibility.
- **`ship-agent`** — Feature archival and lessons learned specialist (Phase 4).
- **`spark-engineer`** — PySpark and Spark SQL specialist for distributed data processing at scale.
- **`spark-performance-analyzer`** — Spark performance optimization specialist for tuning memory, partitioning, joins, and I/O.
- **`spark-specialist`** — Apache Spark SME for performance optimization, architecture design, and troubleshooting.
- **`spark-streaming-architect`** — Spark Structured Streaming expert for real-time pipelines, Kafka integration, and stream processing. Uses KB + MCP validation.
- **`spark-troubleshooter`** — Spark debugging specialist for diagnosing OOM errors, data skew, shuffle failures, and job hangs.
- **`sql-optimizer`** — Cross-dialect SQL optimization specialist for query plans, window functions, and performance tuning.
- **`streaming-engineer`** — Stream processing specialist for Flink, Kafka, Spark Streaming, RisingWave, and CDC pipelines.
- **`supabase-specialist`** — Elite Supabase specialist for pgvector, RLS, Edge Functions, Auth, Realtime, and database design.
- **`test-generator`** — Test automation expert for Python. Generates pytest unit tests, integration tests, and fixtures.
- **`the-planner`** — Strategic AI architect that creates comprehensive implementation plans.

## D. Model Routing Strategy

Cost-optimize by matching task complexity to model capability.

| Model | Share | Use For |
|-------|-------|---------|
| Haiku | ~70% | File exploration, pattern matching, documentation lookup, simple code generation |
| Sonnet | ~20% | Code review, feature implementation, refactoring, API development, most T1/T2 agents |
| Opus | ~10% | Architectural decisions, complex system design, security reviews, T3 agents |

**Override rules:**
- Agent frontmatter `model:` wins over task-complexity heuristics.
- Tasks touching production data or security escalate to Opus.
- Confidence below 0.75 on Sonnet → retry on Opus before asking user.

## E. Composition Hints

**Parallel** (independent work, different files):
- `dbt-specialist` + `test-generator`
- `code-reviewer` + `data-quality-analyst`
- `schema-designer` + `pipeline-architect`

**Serial** (output feeds next step):
- `schema-designer` → `dbt-specialist`
- `pipeline-architect` → `airflow-specialist`
- `define-agent` → `design-agent` → `build-agent`

**Background** (non-blocking):
- `codebase-explorer`, `code-documenter`, `kb-architect`

## F. How Routing Works

1. **File-pattern signal** — agent's `kb_domains` implies file types (e.g., `dbt` → `models/**/*.sql`).
2. **Intent signal** — the one-liner in `description` is the semantic anchor.
3. **Context signal** — agent's `category` scopes the match to the right domain.
4. **Escalation signal** — `escalation_rules.target` provides the handoff graph.

To change routing, edit the **agent's frontmatter**, not this file. Then run:

```bash
python3 scripts/generate-agent-router.py
```
