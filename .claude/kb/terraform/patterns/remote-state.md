# Remote State Pattern

> **Purpose**: GCS backend configuration for state management and team collaboration
> **MCP Validated**: 2026-01-25

## When to Use

- Team collaboration on infrastructure
- CI/CD pipeline deployments
- State locking to prevent conflicts
- State versioning for recovery
- Multiple environments with isolated state

## Implementation

### Bootstrap State Bucket (Run Once)

```hcl
# bootstrap/main.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

# State bucket
resource "google_storage_bucket" "terraform_state" {
  name          = "tf-state-${var.project_id}"
  location      = "US"
  project       = var.project_id
  force_destroy = false

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  # Keep 10 versions of state file
  lifecycle_rule {
    condition {
      num_newer_versions = 10
    }
    action {
      type = "Delete"
    }
  }

  # Delete non-current versions after 30 days
  lifecycle_rule {
    condition {
      age         = 30
      with_state  = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    purpose    = "terraform-state"
    managed_by = "terraform"
  }
}

output "state_bucket_name" {
  value = google_storage_bucket.terraform_state.name
}
```

### Backend Configuration

```hcl
# backend.tf (in each environment)
terraform {
  backend "gcs" {
    bucket = "tf-state-myproject-123"
    prefix = "invoice-pipeline/prod"
  }
}
```

### Environment-Specific Backends

```text
environments/
├── dev/
│   ├── backend.tf    # prefix = "invoice-pipeline/dev"
│   └── main.tf
├── staging/
│   ├── backend.tf    # prefix = "invoice-pipeline/staging"
│   └── main.tf
└── prod/
    ├── backend.tf    # prefix = "invoice-pipeline/prod"
    └── main.tf
```

## Terragrunt Configuration

For DRY backend configuration with Terragrunt:

```hcl
# terragrunt.hcl (root)
remote_state {
  backend = "gcs"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
  config = {
    project  = "myproject-123"
    location = "us-central1"
    bucket   = "tf-state-myproject-123"
    prefix   = "${path_relative_to_include()}/terraform.tfstate"
  }
}
```

```hcl
# environments/prod/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/invoice-pipeline"
}

inputs = {
  environment = "prod"
  project_id  = "myproject-123"
}
```

## State Locking

GCS backend automatically provides state locking:

```bash
# If lock is stuck (emergency only)
terraform force-unlock LOCK_ID
```

## Reading Remote State

```hcl
data "terraform_remote_state" "network" {
  backend = "gcs"
  config = { bucket = "tf-state-myproject-123", prefix = "network/prod" }
}
# Use: data.terraform_remote_state.network.outputs.vpc_connector_id
```

## Best Practices

| Practice | Why |
|----------|-----|
| One bucket per project | Simplify IAM |
| Prefix per environment | Isolate state |
| Enable versioning | Recovery |
| Restrict bucket access | Security |
| Use lifecycle rules | Cost control |

## Related

- [State Concept](../concepts/state.md)
- [Workspaces Concept](../concepts/workspaces.md)
- [Providers Concept](../concepts/providers.md)
