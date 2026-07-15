# Tutorials

Step-by-step walkthroughs for common AgentSpec workflows.

## Available Tutorials

### Data Engineering Workflows

- [Your First Data Pipeline](../getting-started/) — 10 min, Beginner
- [Build a dbt Staging + Mart Layer](#build-a-dbt-staging--mart-layer)
- [Design a Star Schema with /schema](#design-a-star-schema-with-schema)
- [Add Data Quality with Great Expectations](#add-data-quality-with-great-expectations)
- [Build a PySpark Processing Job](#build-a-pyspark-processing-job)
- [Create a Kafka Streaming Pipeline](#create-a-kafka-streaming-pipeline)
- [Build a RAG Pipeline with /ai-pipeline](#build-a-rag-pipeline-with-ai-pipeline)

### SDD Workflow Basics

- [Using /iterate When Requirements Change](#using-iterate-when-requirements-change)
- [Building with Agent Delegation](#building-with-agent-delegation)
- [Creating a Knowledge Base Domain](#creating-a-knowledge-base-domain)

---

## Data Engineering Workflows

### Build a dbt Staging + Mart Layer

**Time:** 15 min | **Agents:** `define-agent`, `design-agent`, `build-agent`, `dbt-specialist`

Use the full SDD workflow to produce a production-ready incremental staging model.

**Step 1 — Capture requirements**

```bash
claude> /define "dbt staging model for raw_orders with incremental refresh"
```

`define-agent` creates `.claude/sdd/features/DEFINE_STG_ORDERS.md` with functional requirements, grain definition, and acceptance criteria. Review it before proceeding.

**Step 2 — Design the architecture**

```bash
claude> /design STG_ORDERS
```

`design-agent` produces a file manifest that maps `models/staging/stg_orders.sql` and `models/marts/mart_revenue.sql` to `@dbt-specialist`, along with schema contract and incremental strategy selection (merge on `order_id`).

**Step 3 — Build**

```bash
claude> /build STG_ORDERS
```

`build-agent` reads the manifest, delegates `stg_orders.sql` to `dbt-specialist`, and writes the files. Example output for the staging model:

```sql
-- models/staging/stg_orders.sql
{{
  config(
    materialized = 'incremental',
    unique_key    = 'order_id',
    incremental_strategy = 'merge'
  )
}}

with source as (
    select * from {{ source('raw', 'orders') }}
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}
),

renamed as (
    select
        order_id,
        customer_id,
        order_date::date                  as order_date,
        total_amount_cents / 100.0        as order_total,
        status,
        loaded_at
    from source
)

select * from renamed
```

`build-agent` also generates `models/staging/stg_orders.yml` with `not_null` and `unique` tests on `order_id`.

**Step 4 — Ship**

```bash
claude> /ship STG_ORDERS
```

`ship-agent` archives the SDD documents to `.claude/sdd/archive/` and writes a BUILD_REPORT with lessons learned.

---

### Design a Star Schema with /schema

**Time:** 10 min | **Agent:** `schema-designer`

Skip the SDD workflow when you just need a dimensional model fast.

**Step 1 — Run the command**

```bash
claude> /schema "Star schema for e-commerce: orders, customers, products"
```

**Step 2 — schema-designer produces the model**

`schema-designer` identifies the grain, creates dimension and fact tables, and outputs DDL for your target platform. Example output:

```
Grain: one row per order line item
Fact:  fct_orders (order_id, customer_key, product_key, order_date_key,
                   quantity, unit_price, total_amount)

Dimensions:
  dim_customers (customer_key, customer_id, full_name, email,
                 country, city, created_date)
  dim_products  (product_key, product_id, product_name, category,
                 subcategory, unit_cost, is_active)
  dim_date      (date_key, full_date, year, quarter, month,
                 week_of_year, is_weekend)
```

**Step 3 — Review and extend**

Ask follow-up questions in the same session:

```bash
claude> "Add SCD Type 2 to dim_customers to track address changes"
claude> "Generate BigQuery DDL for all tables"
```

`schema-designer` handles SCD Type 2 surrogate key patterns, effective dates, and current-row flags without leaving the conversation.

---

### Add Data Quality with Great Expectations

**Time:** 10 min | **Agent:** `data-quality-analyst`

**Step 1 — Point at a model file**

```bash
claude> /data-quality models/staging/stg_orders.sql
```

**Step 2 — data-quality-analyst generates the suite**

The agent reads the model's column definitions and business rules, then produces two artifacts.

A Great Expectations suite (`expectations/stg_orders.json`):

```json
{
  "expectation_suite_name": "stg_orders",
  "expectations": [
    {
      "expectation_type": "expect_column_values_to_not_be_null",
      "kwargs": { "column": "order_id" }
    },
    {
      "expectation_type": "expect_column_values_to_be_unique",
      "kwargs": { "column": "order_id" }
    },
    {
      "expectation_type": "expect_column_values_to_be_between",
      "kwargs": { "column": "order_total", "min_value": 0 }
    },
    {
      "expectation_type": "expect_column_values_to_be_in_set",
      "kwargs": {
        "column": "status",
        "value_set": ["pending", "confirmed", "shipped", "cancelled"]
      }
    }
  ]
}
```

A dbt test YAML (`models/staging/stg_orders.yml`):

```yaml
models:
  - name: stg_orders
    columns:
      - name: order_id
        tests: [not_null, unique]
      - name: order_total
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
      - name: status
        tests:
          - accepted_values:
              values: [pending, confirmed, shipped, cancelled]
```

**Step 3 — Generate checks for a description instead of a file**

```bash
claude> /data-quality "Quality checks for customer dimension with SCD Type 2"
```

---

### Build a PySpark Processing Job

**Time:** 15 min | **Agents:** `define-agent`, `build-agent`, `spark-engineer`

**Step 1 — Define the job**

```bash
claude> /define "PySpark job to deduplicate and SCD merge customer events"
```

`define-agent` captures the deduplication key (`customer_id + event_timestamp`), merge strategy (SCD Type 2 on `email` and `address`), and target format (Delta Lake).

**Step 2 — Build it**

```bash
claude> /build CUSTOMER_EVENTS
```

`build-agent` delegates to `spark-engineer`, which produces a structured job:

```
jobs/
  customer_events/
    job.py            # entry point with argument parsing
    transforms.py     # deduplication and SCD merge logic
    schema.py         # StructType definitions
    tests/
      test_transforms.py
```

`spark-engineer` applies KB patterns: window-based deduplication with `row_number()`, Delta `MERGE INTO` for SCD Type 2, and partition pruning on `event_date`.

**Step 3 — Run and verify**

```bash
spark-submit --master local[4] jobs/customer_events/job.py \
  --source s3://raw/customer_events/ \
  --target s3://silver/dim_customers/
```

---

### Create a Kafka Streaming Pipeline

**Time:** 15 min | **Agents:** `define-agent`, `design-agent`, `streaming-engineer`, `spark-streaming-architect`

**Step 1 — Define the pipeline**

```bash
claude> /define "Real-time order events from Kafka to lakehouse"
```

`define-agent` captures source topic (`orders.created`), target (Delta Lake `silver.orders`), latency SLA (sub-60s), and late data tolerance (10 min watermark).

**Step 2 — Design the architecture**

```bash
claude> /design ORDER_STREAM
```

`design-agent` creates the architecture document and assigns:

- `streaming-engineer` — Kafka consumer, schema registry integration, DLQ handling
- `spark-streaming-architect` — Structured Streaming job, watermarking, checkpoint config

The architecture document shows the pipeline topology:

```
Kafka (orders.created)
  -> Structured Streaming job
       -> Schema validation (Avro / Schema Registry)
       -> Watermark: 10 min on event_time
       -> Append mode -> Delta Lake silver.orders
  -> Dead-letter queue -> Kafka (orders.dlq)
```

**Step 3 — Build**

```bash
claude> /build ORDER_STREAM
```

`build-agent` delegates to both agents. `spark-streaming-architect` produces the Structured Streaming job with checkpoint location, trigger interval, and watermark configuration. `streaming-engineer` produces the Kafka source options and DLQ handler.

---

### Build a RAG Pipeline with /ai-pipeline

**Time:** 15 min | **Agents:** `ai-data-engineer`, `qdrant-specialist`

**Step 1 — Run the command**

```bash
claude> /ai-pipeline "RAG pipeline for internal knowledge base with Qdrant"
```

**Step 2 — ai-data-engineer designs the layers**

The agent structures the pipeline into two layers:

**Embedding layer** (`pipelines/embedding/`):

```
documents/          # raw PDFs, markdown, Confluence exports
  loader.py         # LangChain document loaders
  chunker.py        # recursive text splitter (512 tokens, 50 overlap)
  embedder.py       # OpenAI text-embedding-3-small (1536 dim)
  indexer.py        # Qdrant upsert with payload metadata
```

**Retrieval layer** (`pipelines/retrieval/`):

```
retriever.py        # dense search + metadata filtering
reranker.py         # cross-encoder reranking (optional)
generator.py        # prompt assembly + LLM call
pipeline.py         # end-to-end RAG chain
```

**Step 3 — Qdrant collection setup**

`qdrant-specialist` handles the collection configuration:

```python
client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    optimizers_config=OptimizersConfigDiff(indexing_threshold=20000),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(type=ScalarType.INT8, quantile=0.99)
    )
)
```

Payload indexes are created on `source`, `doc_type`, and `created_at` to enable filtered search without full scans.

---

## SDD Workflow Basics

### Using /iterate When Requirements Change

**Time:** 5 min | **Agent:** `iterate-agent`

`iterate-agent` handles mid-stream requirement changes with cascade detection. It reads the changed document and identifies which downstream SDD files need updates.

**Scenario:** A stakeholder adds a 3-day late-arriving data requirement after design has started.

**Step 1 — Update with /iterate**

```bash
claude> /iterate .claude/sdd/features/DEFINE_ORDERS_PIPELINE.md \
  "Add support for late-arriving data with 3-day lookback"
```

**Step 2 — Cascade detection output**

`iterate-agent` updates the DEFINE document and reports which downstream files are affected:

```
Updated: DEFINE_ORDERS_PIPELINE.md
  + Added: late_arriving_data requirement (3-day lookback window)
  + Updated: acceptance_criteria — added late data SLA

Cascade detected:
  DESIGN_ORDERS_PIPELINE.md   — watermark config must change
  BUILD_REPORT_ORDERS.md      — not yet created, no action needed
```

**Step 3 — Apply the cascade**

```bash
claude> /iterate .claude/sdd/features/DESIGN_ORDERS_PIPELINE.md \
  "Update watermark to 3 days to match new late data requirement"
```

Each iteration is focused and explicit. `iterate-agent` never silently updates documents you did not ask about — it reports what changed and what is pending.

---

### Building with Agent Delegation

**Time:** 15 min | **Agent:** `build-agent`

`build-agent` reads the file manifest from a DESIGN document and assigns each file to the appropriate specialist agent.

**Example DESIGN manifest:**

```yaml
files:
  - path: models/staging/stg_orders.sql
    agent: "@dbt-specialist"
    pattern: incremental-model

  - path: jobs/customer_events/job.py
    agent: "@spark-engineer"
    pattern: deduplication

  - path: models/staging/stg_orders.yml
    agent: "@dbt-specialist"
    pattern: testing-framework

  - path: tests/test_transforms.py
    agent: "@test-generator"
    pattern: pytest-fixtures
```

**Running the build**

```bash
claude> /build ORDERS_PIPELINE
```

`build-agent` processes the manifest top to bottom. For each `@agent-name` entry it launches the specialist via the Task tool, passing the KB domain context. For `(general)` entries it writes the file directly using KB patterns.

**What build-agent does not do:**

- It does not write code outside the manifest
- It does not proceed if a specialist returns a confidence score below 0.90
- It does not skip verification — after each file it confirms the output matches the DESIGN spec

---

### Creating a Knowledge Base Domain

**Time:** 10 min | **Agent:** `kb-architect`

Use `/create-kb` to scaffold a complete domain with index, quick-reference, concepts, and patterns. The default is a light single-pass build; add `--validated` for a high-assurance, source-verified build (research with adversarial refutation + an independent fact-check gate, via the `kb-build` skill) when many agents will trust the domain as ground truth.

**Step 1 — Run the command**

```bash
claude> /create-kb redis
# or, for a source-verified build:
claude> /create-kb redis --validated
```

**Step 2 — kb-architect scaffolds the domain**

The agent validates `.claude/kb/_templates/` and `_index.yaml`, then creates:

```
.claude/kb/redis/
  index.md            # domain overview: what, when, scope
  quick-reference.md  # cheat sheet: commands, config, patterns
  concepts/
    data-structures.md
    persistence.md
    pub-sub.md
  patterns/
    caching-patterns.md
    session-store.md
```

**Step 3 — Registry update**

`kb-architect` adds the new domain to `.claude/kb/_index.yaml`:

```yaml
redis:
  description: "Redis data structures, caching, pub/sub, and session patterns"
  concepts: [data-structures, persistence, pub-sub]
  patterns: [caching-patterns, session-store]
  agents: []
```

**Step 4 — Audit existing KB health**

```bash
claude> /create-kb --audit
```

Reports which domains are missing files, have outdated patterns, or are not referenced by any agent.

---

## Common Data Engineering Workflows

### Quick Schema Design

Design a star schema without the full SDD workflow:

```bash
claude> /schema "Star schema for e-commerce: orders, customers, products"
```

`schema-designer` creates dimension/fact tables, grain definitions, and DDL for your target platform.

### Quick Pipeline Scaffold

Scaffold an Airflow DAG:

```bash
claude> /pipeline "Daily orders ETL: Postgres -> staging -> dbt -> Snowflake marts"
```

`pipeline-architect` creates DAG code with task dependencies, sensors, and error handling.

### Data Quality Rules Generation

Generate quality checks for existing models:

```bash
claude> /data-quality models/staging/stg_orders.sql

claude> /data-quality "Quality checks for customer dimension with SCD Type 2"
```

`data-quality-analyst` generates Great Expectations suites and/or dbt test YAML.

### SQL Review for Anti-Patterns

```bash
claude> /sql-review models/marts/

claude> /sql-review models/staging/stg_orders.sql
```

`code-reviewer` (with DE capability) and `sql-optimizer` check for `SELECT *`, missing partition filters, PII exposure, implicit coercion, and more.

### Legacy ETL Migration

Migrate stored procedures to dbt:

```bash
claude> /migrate legacy/sp_daily_orders.sql

claude> /migrate "Convert Informatica workflows to Airflow + dbt"
```

### Data Contract Authoring

Create producer-consumer agreements:

```bash
claude> /data-contract "Contract between orders team and analytics for mart_revenue"
```

---

## Full SDD Workflow Examples

### Quick Feature with /define + /build

Skip brainstorm when requirements are already clear:

```bash
claude> /define "Add incremental refresh to stg_orders model"

claude> /design STG_ORDERS_INCREMENTAL

claude> /build STG_ORDERS_INCREMENTAL

claude> /ship STG_ORDERS_INCREMENTAL
```

### Updating Requirements Mid-Stream

When a stakeholder changes scope after you have started design:

```bash
claude> /iterate .claude/sdd/features/DEFINE_ORDERS_PIPELINE.md \
  "Add support for late-arriving data with 3-day lookback"
```

`iterate-agent` detects which downstream documents (DESIGN, BUILD_REPORT) need updates and guides you through each cascade.

---

## Code Quality Workflows

### Code Review with Dual AI

```bash
claude> /review

claude> /review --base main

claude> /review --quick
```

---

## What's Next

- [Core Concepts](../concepts/) — understand the mental model
- [Reference](../reference/) — full command, agent, and KB domain catalog
