# GCP Serverless Data Engineering Knowledge Base

> **Purpose**: Reference for serverless data engineering on Google Cloud Platform
> **MCP Validated**: 2026-01-25

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/cloud-run.md](concepts/cloud-run.md) | Serverless container platform |
| [concepts/pubsub.md](concepts/pubsub.md) | Asynchronous messaging service |
| [concepts/gcs.md](concepts/gcs.md) | Object storage with event triggers |
| [concepts/bigquery.md](concepts/bigquery.md) | Data warehouse with streaming inserts |
| [concepts/iam.md](concepts/iam.md) | Identity and access management |
| [concepts/secret-manager.md](concepts/secret-manager.md) | Secrets and credential management |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/event-driven-pipeline.md](patterns/event-driven-pipeline.md) | GCS to Pub/Sub to Cloud Run architecture |
| [patterns/multi-bucket-pipeline.md](patterns/multi-bucket-pipeline.md) | Bucket-per-stage data organization |
| [patterns/pubsub-fanout.md](patterns/pubsub-fanout.md) | One topic to multiple subscribers |
| [patterns/cloud-run-scaling.md](patterns/cloud-run-scaling.md) | Concurrency and min/max instances |
| [patterns/gcs-triggered-workflow.md](patterns/gcs-triggered-workflow.md) | Eventarc triggers from storage events |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Serverless** | Pay-per-use, auto-scaling, no infrastructure management |
| **Event-Driven** | Services react to events, decoupled via Pub/Sub |
| **Immutable Storage** | GCS objects as pipeline triggers |
| **Streaming Inserts** | Real-time data ingestion into BigQuery |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/cloud-run.md, concepts/gcs.md |
| **Intermediate** | patterns/event-driven-pipeline.md, concepts/pubsub.md |
| **Advanced** | patterns/cloud-run-scaling.md, concepts/iam.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| python-developer | patterns/event-driven-pipeline.md | Implement Cloud Run functions |
| infra-agent | patterns/cloud-run-scaling.md | Configure autoscaling |

---

## Project Context

This KB supports the GenAI Invoice Processing Pipeline:

| Component | GCP Service |
|-----------|-------------|
| Input storage | GCS (invoices-input) |
| Processed storage | GCS (invoices-processed) |
| Event bus | Pub/Sub (4 topics) |
| Processing | Cloud Run (4 functions) |
| Data warehouse | BigQuery |
| Secrets | Secret Manager (Gemini API, LangFuse) |
