# Resources and Data Sources

> **Purpose**: Fundamental building blocks of Terraform configurations
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Resources are the most important element in Terraform. Each resource block describes one or more infrastructure objects (VMs, networks, buckets). Data sources allow Terraform to query existing infrastructure or external APIs.

## Resources

### Basic Syntax

```hcl
resource "google_storage_bucket" "invoices_input" {
  name          = "invoices-input-${var.project_id}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}
```

### Resource Behavior

| Action | When |
|--------|------|
| Create | Resource not in state |
| Update | Config differs from state |
| Replace | Immutable attribute changed |
| Destroy | Resource removed from config |

### Meta-Arguments

```hcl
resource "google_pubsub_topic" "pipeline" {
  for_each = toset(["uploaded", "converted", "classified", "extracted"])

  name    = "invoice-${each.key}"
  project = var.project_id

  depends_on = [google_project_service.pubsub]

  lifecycle {
    prevent_destroy = true
  }
}
```

## Data Sources

### Purpose

Query existing resources without managing them.

```hcl
# Read existing project
data "google_project" "current" {
  project_id = var.project_id
}

# Read existing service account
data "google_service_account" "compute" {
  account_id = "compute-default"
}

# Use in resource
resource "google_cloud_run_service" "processor" {
  # ...
  service_account_name = data.google_service_account.compute.email
}
```

### Common GCP Data Sources

| Data Source | Purpose |
|-------------|---------|
| `google_project` | Project metadata |
| `google_compute_network` | Existing VPC |
| `google_service_account` | Existing SA |
| `google_secret_manager_secret_version` | Secret values |
| `google_storage_bucket` | Existing bucket |

## Resource Dependencies

### Implicit (Recommended)

```hcl
resource "google_pubsub_subscription" "processor" {
  name  = "processor-sub"
  topic = google_pubsub_topic.uploaded.name  # Implicit dependency
}
```

### Explicit (When Needed)

```hcl
resource "google_cloud_run_service" "extractor" {
  depends_on = [
    google_project_service.run,
    google_project_service.secretmanager
  ]
  # ...
}
```

## Common Mistakes

### Wrong

```hcl
# Hardcoded project ID
resource "google_storage_bucket" "bad" {
  name = "my-bucket-my-project-123"
}
```

### Correct

```hcl
# Dynamic naming
resource "google_storage_bucket" "good" {
  name = "${var.bucket_prefix}-${var.project_id}"
}
```

## GCP Resource Naming

| Resource | Naming Pattern |
|----------|----------------|
| Buckets | `{prefix}-{project_id}` (globally unique) |
| Topics | `{service}-{action}` |
| Cloud Run | `{service-name}` |
| BigQuery | `{dataset}_{table}` |

## Related

- [Modules](./modules.md)
- [Variables](./variables.md)
- [GCS Module Pattern](../patterns/gcs-module.md)
