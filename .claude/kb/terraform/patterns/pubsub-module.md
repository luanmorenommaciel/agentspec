# Pub/Sub Module Pattern

> **Purpose**: Reusable module for topics, subscriptions, and dead-letter queues
> **MCP Validated**: 2026-01-25

## When to Use

- Create Pub/Sub topics for event-driven architecture
- Configure push subscriptions to Cloud Run
- Implement dead-letter queues for failed messages
- Need consistent retry and backoff policies

## Module Structure

```text
modules/pubsub/
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
└── dlq.tf
```

## Implementation

### Key Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `topic_name` | string | required | Pub/Sub topic name |
| `project_id` | string | required | GCP project ID |
| `message_retention_duration` | string | `"604800s"` | 7 days retention |
| `enable_dead_letter` | bool | `true` | Create DLQ topic |
| `subscriptions` | list(object) | `[]` | Subscription configs |

### main.tf

```hcl
resource "google_pubsub_topic" "topic" {
  name    = var.topic_name
  project = var.project_id
  labels  = var.labels

  message_retention_duration = var.message_retention_duration
}

resource "google_pubsub_subscription" "subscription" {
  for_each = { for sub in var.subscriptions : sub.name => sub }

  name    = each.value.name
  topic   = google_pubsub_topic.topic.name
  project = var.project_id
  labels  = var.labels

  ack_deadline_seconds = each.value.ack_deadline_seconds

  # Push configuration (if endpoint provided)
  dynamic "push_config" {
    for_each = each.value.push_endpoint != null ? [1] : []
    content {
      push_endpoint = each.value.push_endpoint

      oidc_token {
        service_account_email = google_service_account.pubsub_invoker.email
      }
    }
  }

  # Dead letter policy
  dynamic "dead_letter_policy" {
    for_each = each.value.enable_dlq && var.enable_dead_letter ? [1] : []
    content {
      dead_letter_topic     = google_pubsub_topic.dlq[0].id
      max_delivery_attempts = each.value.max_delivery_attempts
    }
  }

  # Retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  # Message filter (optional)
  filter = each.value.filter

  # Expiration policy - never expire
  expiration_policy {
    ttl = ""
  }
}

# Service account for push subscriptions
resource "google_service_account" "pubsub_invoker" {
  account_id   = "${var.topic_name}-invoker"
  display_name = "Pub/Sub Invoker for ${var.topic_name}"
  project      = var.project_id
}
```

### dlq.tf

```hcl
# Dead letter topic
resource "google_pubsub_topic" "dlq" {
  count = var.enable_dead_letter ? 1 : 0

  name    = "${var.topic_name}-dlq"
  project = var.project_id
  labels  = var.labels

  message_retention_duration = "604800s" # 7 days
}

# DLQ subscription for monitoring
resource "google_pubsub_subscription" "dlq_sub" {
  count = var.enable_dead_letter ? 1 : 0

  name    = "${var.topic_name}-dlq-sub"
  topic   = google_pubsub_topic.dlq[0].name
  project = var.project_id

  ack_deadline_seconds = 600 # 10 minutes for manual review

  expiration_policy {
    ttl = ""
  }
}

# Grant Pub/Sub permission to publish to DLQ
resource "google_pubsub_topic_iam_member" "dlq_publisher" {
  count = var.enable_dead_letter ? 1 : 0

  project = var.project_id
  topic   = google_pubsub_topic.dlq[0].name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

data "google_project" "current" {
  project_id = var.project_id
}
```

### outputs.tf

```hcl
output "topic_name" { value = google_pubsub_topic.topic.name }
output "topic_id" { value = google_pubsub_topic.topic.id }
output "dlq_topic_name" { value = var.enable_dead_letter ? google_pubsub_topic.dlq[0].name : null }
```

## Example Usage

```hcl
module "invoice_converted_topic" {
  source = "./modules/pubsub"

  topic_name = "invoice-converted"
  project_id = var.project_id

  subscriptions = [
    {
      name                  = "invoice-classifier-sub"
      push_endpoint         = module.classifier.service_url
      ack_deadline_seconds  = 60
      enable_dlq            = true
      max_delivery_attempts = 5
    }
  ]

  labels = local.common_labels
}
```

## Related

- [Cloud Run Module](./cloud-run-module.md)
- [GCS Module](./gcs-module.md)
- [IAM Module](./iam-module.md)
