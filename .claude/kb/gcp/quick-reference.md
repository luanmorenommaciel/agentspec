# GCP Serverless Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-01-25

## Service Selection

| Use Case | Choose | Why |
|----------|--------|-----|
| Run containers on events | Cloud Run | Serverless, scales to zero |
| Async message passing | Pub/Sub | Decouples producers/consumers |
| Store files with triggers | GCS + Eventarc | Object events to Cloud Run |
| Analytics warehouse | BigQuery | Streaming inserts, SQL |
| Store API keys | Secret Manager | Versioned, encrypted |

## Cloud Run Limits

| Setting | Default | Max |
|---------|---------|-----|
| Request timeout | 5 min | 60 min |
| Max instances | 100 | 1000+ (quota) |
| Min instances | 0 | configurable |
| Concurrency | 80 | 1000 |
| Memory | 512 MB | 32 GB |
| vCPUs | 1 | 8 |

## Pub/Sub Defaults

| Setting | Value | Notes |
|---------|-------|-------|
| Message retention | 7 days | Configurable up to 31 days |
| Ack deadline | 10 sec | Max 600 sec |
| Max message size | 10 MB | Per message |
| Delivery | At-least-once | Deduplication via message ID |

## BigQuery Streaming

| Constraint | Value |
|------------|-------|
| Past partition limit | 31 days |
| Future partition limit | 16 days |
| Max row size | 10 MB |
| Deduplication window | Minutes |

## GCS Event Types

| Event | When Fired |
|-------|------------|
| `google.cloud.storage.object.v1.finalized` | Object created/overwritten |
| `google.cloud.storage.object.v1.deleted` | Object permanently deleted |
| `google.cloud.storage.object.v1.archived` | Object version archived |
| `google.cloud.storage.object.v1.metadataUpdated` | Metadata changed |

## IAM Roles (Least Privilege)

| Task | Role |
|------|------|
| Invoke Cloud Run | `roles/run.invoker` |
| Publish to Pub/Sub | `roles/pubsub.publisher` |
| Subscribe to Pub/Sub | `roles/pubsub.subscriber` |
| Read GCS | `roles/storage.objectViewer` |
| Write GCS | `roles/storage.objectCreator` |
| Insert to BigQuery | `roles/bigquery.dataEditor` |
| Access secrets | `roles/secretmanager.secretAccessor` |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| TIFF to PNG conversion | Cloud Run + GCS trigger |
| Fan-out processing | Pub/Sub + multiple subscribers |
| Structured data storage | BigQuery |
| Unstructured storage | GCS |
| API keys for LLM | Secret Manager |

## Common Pitfalls

| Avoid | Do Instead |
|-------|------------|
| Using default service account | Create dedicated service accounts |
| `SELECT *` on BigQuery | Select specific columns |
| Hardcoding secrets | Use Secret Manager |
| Single bucket for all stages | Bucket-per-stage pattern |
| No dead-letter queue | Configure DLQ on subscriptions |
| Max instances = 0 | Set min instances for latency |

## Related Documentation

| Topic | Path |
|-------|------|
| Cloud Run concepts | `concepts/cloud-run.md` |
| Event-driven pattern | `patterns/event-driven-pipeline.md` |
| Full Index | `index.md` |
