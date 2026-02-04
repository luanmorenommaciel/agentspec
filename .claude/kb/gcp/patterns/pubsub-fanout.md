# Pub/Sub Fan-Out Pattern

> **Purpose**: Distribute one event to multiple consumers for parallel processing
> **MCP Validated**: 2026-01-25

## When to Use

- One event needs multiple independent actions (audit log + processing + notification)
- Consumers have different performance characteristics
- Consumers can fail independently without blocking others
- You need to add new consumers without modifying publishers

## Implementation

```hcl
# Terraform: Fan-out infrastructure
resource "google_pubsub_topic" "invoice_extracted" {
  name = "invoice-extracted"
}

# Subscription 1: Write to BigQuery
resource "google_pubsub_subscription" "to_bigquery" {
  name  = "invoice-extracted-to-bigquery"
  topic = google_pubsub_topic.invoice_extracted.name

  push_config {
    push_endpoint = google_cloud_run_service.bigquery_writer.status[0].url
    oidc_token {
      service_account_email = google_service_account.pubsub_invoker.email
    }
  }

  ack_deadline_seconds = 60
}

# Subscription 2: Send to audit system
resource "google_pubsub_subscription" "to_audit" {
  name  = "invoice-extracted-to-audit"
  topic = google_pubsub_topic.invoice_extracted.name

  push_config {
    push_endpoint = google_cloud_run_service.audit_logger.status[0].url
    oidc_token {
      service_account_email = google_service_account.pubsub_invoker.email
    }
  }

  ack_deadline_seconds = 30
}

# Subscription 3: Direct BigQuery subscription (no code)
resource "google_pubsub_subscription" "to_bigquery_direct" {
  name  = "invoice-extracted-to-bq-direct"
  topic = google_pubsub_topic.invoice_extracted.name

  bigquery_config {
    table          = "${var.project_id}.audit.raw_events"
    write_metadata = true
  }
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ack_deadline_seconds` | 10 | Time for consumer to acknowledge |
| `message_retention_duration` | 7d | How long unacked messages persist |
| `retain_acked_messages` | false | Keep acknowledged messages |
| `enable_message_ordering` | false | Preserve message order |

## Example Usage

```python
# Publisher: Single publish, multiple consumers receive
from google.cloud import pubsub_v1
import json

def publish_extraction_result(project_id: str, invoice_data: dict):
    """Publish extraction result - all subscribers receive copy."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, "invoice-extracted")

    message = json.dumps({
        "invoice_id": invoice_data["invoice_id"],
        "vendor_name": invoice_data["vendor_name"],
        "total_amount": invoice_data["total_amount"],
        "extracted_at": datetime.utcnow().isoformat(),
        "confidence": invoice_data["confidence"]
    }).encode()

    # Each subscriber gets their own copy
    future = publisher.publish(
        topic_path,
        message,
        event_type="invoice.extracted",
        source="invoice-extractor"
    )

    return future.result()

# Consumer 1: BigQuery writer
@functions_framework.cloud_event
def write_to_bigquery(cloud_event):
    """Write extracted invoice to warehouse."""
    data = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))
    insert_to_bigquery(data)

# Consumer 2: Audit logger
@functions_framework.cloud_event
def log_to_audit(cloud_event):
    """Log extraction event for compliance."""
    data = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))
    log_audit_event("invoice_extracted", data)
```

## Fan-Out Topology

```
                    ┌──────────────────────┐
                    │   invoice-extractor  │
                    └──────────┬───────────┘
                               │ publish
                               v
              ┌────────────────────────────────┐
              │  Topic: invoice-extracted      │
              └────────────────┬───────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        v                      v                      v
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Sub: bigquery │    │ Sub: audit    │    │ Sub: bq-raw   │
│     (push)    │    │    (push)     │    │   (direct)    │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        v                    v                    v
  [BQ Writer]         [Audit Logger]        [BQ: audit]
```

## Dead-Letter Handling

```hcl
resource "google_pubsub_topic" "dlq" {
  name = "invoice-extracted-dlq"
}

resource "google_pubsub_subscription" "with_dlq" {
  name  = "invoice-extracted-to-bigquery"
  topic = google_pubsub_topic.invoice_extracted.name

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq.id
    max_delivery_attempts = 5
  }
}
```

## See Also

- [Event-Driven Pipeline](../patterns/event-driven-pipeline.md)
- [Pub/Sub](../concepts/pubsub.md)
- [Cloud Run](../concepts/cloud-run.md)
