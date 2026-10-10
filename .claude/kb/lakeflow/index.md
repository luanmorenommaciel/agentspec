# Databricks Lakeflow Knowledge Base

> **Purpose**: Authoritative reference for Lakeflow Declarative Pipelines (formerly DLT) development.
> **Version Coverage**: Lakeflow Declarative Pipelines GA (July 2025), releases through Feb 2026 (DBR 16.4/17.3)
> **Key Update**: Contributed to Apache Spark as "Spark Declarative Pipelines" (DAIS 2025)
> **MCP Validated**: 2026-03-26

## Quick Navigation

### Concepts (Explanatory, < 150 lines)

| File | Purpose |
|------|---------|
| [concepts/core-concepts.md](concepts/core-concepts.md) | Streaming tables, materialized views, Lakeflow fundamentals |
| [concepts/getting-started.md](concepts/getting-started.md) | Tutorial for first pipeline |
| [concepts/cdc-fundamentals.md](concepts/cdc-fundamentals.md) | Change Data Capture with APPLY CHANGES |
| [concepts/deployment-model.md](concepts/deployment-model.md) | Deployment modes, configuration, lifecycle with DABs |
| [concepts/expectations-model.md](concepts/expectations-model.md) | Data quality constraints on records flowing through a pipeline |

### Patterns (Code-focused, < 200 lines)

| File | Purpose |
|------|---------|
| [patterns/python-decorators.md](patterns/python-decorators.md) | @dlt.table, @dlt.view, @dlt.expect decorators |
| [patterns/python-streaming.md](patterns/python-streaming.md) | Streaming patterns, Auto Loader, Medallion |
| [patterns/sql-tables.md](patterns/sql-tables.md) | CREATE TABLE statements, TBLPROPERTIES |
| [patterns/sql-streaming.md](patterns/sql-streaming.md) | STREAM syntax, joins, aggregations |
| [patterns/cdc-apply-changes.md](patterns/cdc-apply-changes.md) | APPLY CHANGES, SCD Type 1/2 |
| [patterns/cdc-example.md](patterns/cdc-example.md) | Complete CDC examples (Python/SQL) |
| [patterns/expectations.md](patterns/expectations.md) | Basic data quality expectations |
| [patterns/expectations-advanced.md](patterns/expectations-advanced.md) | Grouped expectations, common patterns |
| [patterns/bronze-ingestion.md](patterns/bronze-ingestion.md) | S3 Parquet ingestion, Auto Loader config |
| [patterns/silver-cleansing.md](patterns/silver-cleansing.md) | Type casting, PII masking, deduplication |
| [patterns/gold-aggregation.md](patterns/gold-aggregation.md) | KPIs, aggregations, time-series |
| [patterns/dabs-deployment.md](patterns/dabs-deployment.md) | Databricks Asset Bundles configuration |

### Reference (Comprehensive, no line limit)

| File | Purpose |
|------|---------|
| [reference/pipeline-configuration.md](reference/pipeline-configuration.md) | Pipeline settings, clusters |
| [reference/serverless-pipelines.md](reference/serverless-pipelines.md) | Serverless compute |
| [reference/materialized-views.md](reference/materialized-views.md) | MV optimization |
| [reference/stateful-processing.md](reference/stateful-processing.md) | Streaming state, watermarks |
| [reference/parameters.md](reference/parameters.md) | Pipeline parameters |
| [reference/unity-catalog.md](reference/unity-catalog.md) | UC integration |
| [reference/limitations.md](reference/limitations.md) | Known limitations |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Streaming Table** | Incrementally processes new data |
| **Materialized View** | Batch-refreshed aggregate table |
| **Expectation** | Data quality constraint |
| **AUTO CDC** | Automatic change data capture (SCD Type 1 now supported) |
| **SCD Type 1/2** | Slowly Changing Dimension patterns |
| **Move Tables** | Move MVs/STs between pipelines (GA, 2025.29) |
| **Type Widening** | Safe column type broadening without pipeline reset (Feb 2026) |
| **Multi-Catalog** | Publish to multiple catalogs/schemas from single pipeline |
| **Spark Declarative Pipelines** | Open-source contribution to Apache Spark (DAIS 2025) |

## Common Patterns

### Medallion Architecture
```
Bronze (Raw) -> Silver (Cleaned) -> Gold (Business)
```

### Data Quality Strategy
```
Bronze: WARN  -> Track issues
Silver: DROP  -> Remove bad data
Gold:   FAIL  -> Strict validation
```

### Recent Release Highlights

| Release | Key Feature |
|---------|-------------|
| 2025.04 (Jan 2025) | Multi-catalog/schema support, LIVE schema no longer required |
| 2025.29 (Jul 2025) | Move Tables between pipelines (GA), ALTER commands on MVs/STs |
| 2025.30 (Jul 2025) | AUTO CDC: multiple flows per target, one-time backfills, SQL support |
| Feb 2026 | Type widening for Delta tables, SCD Type 1 with AUTO CDC |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/core-concepts.md -> concepts/getting-started.md |
| **Intermediate** | patterns/python-decorators.md -> patterns/expectations.md -> patterns/cdc-apply-changes.md |
| **Advanced** | reference/stateful-processing.md -> reference/materialized-views.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| lakeflow-architect | patterns/, concepts/ | Pipeline design |
| lakeflow-expert | All files | Comprehensive guidance |
| lakeflow-pipeline-builder | patterns/bronze-*, patterns/silver-*, patterns/gold-*, patterns/dabs-* | Actual pipeline implementation |
