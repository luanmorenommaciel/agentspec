# IAM Module Pattern

> **Purpose**: Service accounts and IAM bindings with least privilege
> **MCP Validated**: 2026-01-25

## When to Use

- Create dedicated service accounts per service
- Apply least-privilege IAM bindings
- Manage cross-service permissions
- Implement workload identity for GKE

## Module Structure

```text
modules/iam/
├── main.tf
├── variables.tf
├── outputs.tf
└── versions.tf
```

## Implementation

### Key Variables

| Variable | Type | Description |
|----------|------|-------------|
| `project_id` | string | GCP project ID |
| `service_accounts` | list(object) | Service accounts with roles |
| `bucket_iam_bindings` | list(object) | Bucket-level IAM |
| `pubsub_iam_bindings` | list(object) | Topic-level IAM |

### main.tf

```hcl
# Service Accounts
resource "google_service_account" "service_accounts" {
  for_each = { for sa in var.service_accounts : sa.account_id => sa }

  account_id   = each.value.account_id
  display_name = each.value.display_name
  description  = each.value.description
  project      = var.project_id
}

# Project IAM bindings for service accounts
resource "google_project_iam_member" "sa_roles" {
  for_each = {
    for binding in flatten([
      for sa in var.service_accounts : [
        for role in sa.roles : {
          key    = "${sa.account_id}-${role}"
          sa_id  = sa.account_id
          role   = role
        }
      ]
    ]) : binding.key => binding
  }

  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.service_accounts[each.value.sa_id].email}"
}

# Project-level IAM bindings
resource "google_project_iam_binding" "project_bindings" {
  for_each = { for binding in var.project_iam_bindings : binding.role => binding }

  project = var.project_id
  role    = each.value.role
  members = each.value.members
}

# Bucket IAM bindings
resource "google_storage_bucket_iam_member" "bucket_bindings" {
  for_each = {
    for binding in flatten([
      for b in var.bucket_iam_bindings : [
        for member in b.members : {
          key    = "${b.bucket}-${b.role}-${member}"
          bucket = b.bucket
          role   = b.role
          member = member
        }
      ]
    ]) : binding.key => binding
  }

  bucket = each.value.bucket
  role   = each.value.role
  member = each.value.member
}

# Pub/Sub IAM bindings
resource "google_pubsub_topic_iam_member" "pubsub_bindings" {
  for_each = {
    for binding in flatten([
      for t in var.pubsub_iam_bindings : [
        for member in t.members : {
          key    = "${t.topic}-${t.role}-${member}"
          topic  = t.topic
          role   = t.role
          member = member
        }
      ]
    ]) : binding.key => binding
  }

  project = var.project_id
  topic   = each.value.topic
  role    = each.value.role
  member  = each.value.member
}
```

### outputs.tf

```hcl
output "service_account_emails" {
  description = "Map of service account emails"
  value = {
    for k, v in google_service_account.service_accounts : k => v.email
  }
}

output "service_account_ids" {
  description = "Map of service account IDs"
  value = {
    for k, v in google_service_account.service_accounts : k => v.id
  }
}
```

## Example Usage

```hcl
module "pipeline_iam" {
  source = "./modules/iam"

  project_id = var.project_id

  service_accounts = [
    {
      account_id   = "tiff-converter"
      display_name = "TIFF to PNG Converter"
      roles        = ["roles/storage.objectViewer", "roles/storage.objectCreator", "roles/pubsub.publisher"]
    },
    {
      account_id   = "data-extractor"
      display_name = "Data Extractor"
      roles        = ["roles/storage.objectViewer", "roles/pubsub.publisher", "roles/secretmanager.secretAccessor"]
    },
    {
      account_id   = "bigquery-writer"
      display_name = "BigQuery Writer"
      roles        = ["roles/bigquery.dataEditor"]
    }
  ]
}
```

## Least Privilege Reference

| Service | Required Roles |
|---------|----------------|
| Read GCS | `roles/storage.objectViewer` |
| Write GCS | `roles/storage.objectCreator` |
| Publish Pub/Sub | `roles/pubsub.publisher` |
| Invoke Cloud Run | `roles/run.invoker` |
| Write BigQuery | `roles/bigquery.dataEditor` |
| Access Secrets | `roles/secretmanager.secretAccessor` |
| Use Vertex AI | `roles/aiplatform.user` |

## Related

- [Cloud Run Module](./cloud-run-module.md)
- [Pub/Sub Module](./pubsub-module.md)
- [Providers Concept](../concepts/providers.md)
