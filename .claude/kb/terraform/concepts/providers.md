# Providers

> **Purpose**: Plugins that enable Terraform to interact with cloud APIs
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Providers are plugins that Terraform uses to create and manage resources. Each provider offers a set of resource types and data sources. The Google provider enables management of GCP infrastructure.

## GCP Provider Configuration

### Basic Setup

```hcl
# versions.tf
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# providers.tf
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
```

## Authentication Methods

| Method | Use Case | Configuration |
|--------|----------|---------------|
| Application Default Credentials | Local dev, Cloud Shell | `gcloud auth application-default login` |
| Service Account Key | CI/CD pipelines | `GOOGLE_CREDENTIALS` env var |
| Workload Identity | GKE, Cloud Run | Automatic via metadata |
| Impersonation | Cross-project access | `impersonate_service_account` |

### Service Account Authentication

```hcl
provider "google" {
  project     = var.project_id
  region      = var.region
  credentials = file(var.credentials_file)
}
```

### Impersonation (Recommended for CI/CD)

```hcl
provider "google" {
  project = var.project_id
  region  = var.region

  impersonate_service_account = "terraform@${var.project_id}.iam.gserviceaccount.com"
}
```

## Required APIs

Enable APIs before creating resources:

```hcl
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "secretmanager.googleapis.com",
    "eventarc.googleapis.com"
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}
```

## Version Pinning

| Strategy | Example | Use Case |
|----------|---------|----------|
| Pessimistic | `~> 5.0` | Allow patch updates |
| Exact | `= 5.10.0` | Maximum stability |
| Range | `>= 5.0, < 6.0` | Major version lock |

## Common Mistakes

| Wrong | Correct |
|-------|---------|
| Hardcoded credentials in code | Use `GOOGLE_CREDENTIALS` env or ADC |
| Provider config in modules | Configure only in root module |

## Related

- [State](./state.md) | [Remote State](../patterns/remote-state.md) | [IAM Module](../patterns/iam-module.md)
