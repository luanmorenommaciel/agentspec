# State

> **Purpose**: Source of truth for managed infrastructure
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Terraform state is a JSON file that maps configuration to real-world resources. It tracks resource IDs, dependencies, and metadata. Without state, Terraform cannot know which resources it manages.

## State Purpose

| Function | Description |
|----------|-------------|
| Resource mapping | Links config to actual resources |
| Metadata storage | Tracks dependencies and attributes |
| Performance | Caches resource data |
| Collaboration | Enables team workflows |

## Local vs Remote State

### Local State (Development Only)

```hcl
# Default - state stored in terraform.tfstate
# DO NOT commit to version control
```

### Remote State (Production)

```hcl
terraform {
  backend "gcs" {
    bucket = "tf-state-${var.project_id}"
    prefix = "terraform/state"
  }
}
```

## GCS Backend Configuration

### Backend Setup

```hcl
# backend.tf
terraform {
  backend "gcs" {
    bucket = "tf-state-myproject"
    prefix = "env/prod"
  }
}
```

### Create State Bucket

```hcl
# bootstrap/main.tf - Run once manually
resource "google_storage_bucket" "terraform_state" {
  name          = "tf-state-${var.project_id}"
  location      = "US"
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 5
    }
    action {
      type = "Delete"
    }
  }
}
```

## State Locking

GCS backend provides automatic state locking to prevent concurrent modifications:

```hcl
terraform {
  backend "gcs" {
    bucket = "tf-state-myproject"
    prefix = "env/prod"
    # Locking is automatic via GCS
  }
}
```

## State Commands

| Command | Purpose |
|---------|---------|
| `terraform state list` | List all resources |
| `terraform state show <resource>` | Show resource details |
| `terraform state mv` | Rename/move resource |
| `terraform state rm` | Remove from state (not infra) |
| `terraform state pull` | Download remote state |
| `terraform state push` | Upload state (dangerous) |

## State Best Practices

| Practice | Why |
|----------|-----|
| Use remote backend | Team collaboration, locking |
| Enable versioning | Recovery from corruption |
| Encrypt at rest | Sensitive data protection |
| Limit state size | Keep under 100 resources |
| Separate environments | Isolation and blast radius |

## Reading Remote State

Access outputs from other configurations:

```hcl
data "terraform_remote_state" "network" {
  backend = "gcs"
  config = {
    bucket = "tf-state-myproject"
    prefix = "network/prod"
  }
}

# Use outputs
resource "google_cloud_run_service" "api" {
  # ...
  vpc_connector = data.terraform_remote_state.network.outputs.vpc_connector_id
}
```

## Common Mistakes

| Wrong | Correct |
|-------|---------|
| State in git | Use GCS backend, add `*.tfstate` to `.gitignore` |
| No versioning | Enable bucket versioning for recovery |

## Related

- [Providers](./providers.md) | [Remote State](../patterns/remote-state.md) | [Workspaces](./workspaces.md)
