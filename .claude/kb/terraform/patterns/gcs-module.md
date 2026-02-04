# GCS Module Pattern

> **Purpose**: Reusable module for buckets with lifecycle rules and notifications
> **MCP Validated**: 2026-01-25

## When to Use

- Create GCS buckets for data pipelines
- Configure lifecycle rules for cost optimization
- Set up Eventarc notifications to Cloud Run
- Implement bucket-per-stage pattern

## Module Structure

```text
modules/gcs/
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
└── notification.tf
```

## Implementation

### Key Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `bucket_name` | string | required | Globally unique bucket name |
| `project_id` | string | required | GCP project ID |
| `location` | string | `"US"` | Bucket location |
| `storage_class` | string | `"STANDARD"` | Storage class |
| `versioning_enabled` | bool | `true` | Enable versioning |
| `lifecycle_rules` | list(object) | `[]` | Lifecycle rules |
| `notification_topic` | string | `null` | Pub/Sub topic for events |

### main.tf

```hcl
resource "google_storage_bucket" "bucket" {
  name          = var.bucket_name
  project       = var.project_id
  location      = var.location
  storage_class = var.storage_class
  force_destroy = var.force_destroy
  labels        = var.labels

  uniform_bucket_level_access = true

  versioning {
    enabled = var.versioning_enabled
  }

  dynamic "lifecycle_rule" {
    for_each = var.lifecycle_rules
    content {
      action {
        type          = lifecycle_rule.value.action_type
        storage_class = lifecycle_rule.value.action_storage_class
      }
      condition {
        age                   = lifecycle_rule.value.condition_age
        num_newer_versions    = lifecycle_rule.value.condition_num_newer
        matches_prefix        = lifecycle_rule.value.condition_prefix
      }
    }
  }
}
```

### notification.tf

```hcl
# Pub/Sub notification for bucket events
resource "google_storage_notification" "notification" {
  count = var.notification_topic != null ? 1 : 0

  bucket         = google_storage_bucket.bucket.name
  payload_format = "JSON_API_V1"
  topic          = var.notification_topic
  event_types    = var.notification_events

  depends_on = [google_pubsub_topic_iam_member.gcs_publisher]
}

# Grant GCS permission to publish to topic
resource "google_pubsub_topic_iam_member" "gcs_publisher" {
  count = var.notification_topic != null ? 1 : 0

  project = var.project_id
  topic   = var.notification_topic
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${data.google_project.current.number}@gs-project-accounts.iam.gserviceaccount.com"
}

data "google_project" "current" {
  project_id = var.project_id
}
```

### outputs.tf

```hcl
output "bucket_name" {
  description = "Name of the bucket"
  value       = google_storage_bucket.bucket.name
}

output "bucket_url" {
  description = "GCS URL of the bucket"
  value       = google_storage_bucket.bucket.url
}

output "bucket_self_link" {
  description = "Self link of the bucket"
  value       = google_storage_bucket.bucket.self_link
}
```

## Example Usage

```hcl
# Input bucket with notifications
module "invoices_input" {
  source = "./modules/gcs"

  bucket_name = "invoices-input-${var.project_id}"
  project_id  = var.project_id
  location    = "US"

  versioning_enabled = true
  force_destroy      = false

  lifecycle_rules = [
    {
      action_type   = "Delete"
      condition_age = 90  # Delete after 90 days
    }
  ]

  notification_topic  = google_pubsub_topic.uploaded.id
  notification_events = ["OBJECT_FINALIZE"]

  labels = local.common_labels
}

# Processed bucket with archival lifecycle
module "invoices_processed" {
  source = "./modules/gcs"

  bucket_name = "invoices-processed-${var.project_id}"
  project_id  = var.project_id

  lifecycle_rules = [
    { action_type = "SetStorageClass", action_storage_class = "NEARLINE", condition_age = 30 },
    { action_type = "SetStorageClass", action_storage_class = "COLDLINE", condition_age = 90 },
    { action_type = "Delete", condition_age = 365 }
  ]
}
```

## Related

- [Pub/Sub Module](./pubsub-module.md)
- [Cloud Run Module](./cloud-run-module.md)
- [Resources Concept](../concepts/resources.md)
