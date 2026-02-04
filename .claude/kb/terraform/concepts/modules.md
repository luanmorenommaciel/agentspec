# Modules

> **Purpose**: Reusable, composable infrastructure packages
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Modules are containers for multiple resources that are used together. A module consists of a collection of `.tf` files in a directory. Modules are the main way to package and reuse resource configurations.

## Module Structure

```text
modules/
└── cloud-run-service/
    ├── main.tf          # Resource definitions
    ├── variables.tf     # Input variables
    ├── outputs.tf       # Output values
    ├── versions.tf      # Provider requirements
    └── README.md        # Documentation
```

## Standard Module Pattern

### variables.tf

```hcl
variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
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

variable "image" {
  description = "Container image to deploy"
  type        = string
}

variable "env_vars" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}
```

### main.tf

```hcl
resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    spec {
      containers {
        image = var.image

        dynamic "env" {
          for_each = var.env_vars
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }
}
```

### outputs.tf

```hcl
output "service_url" {
  description = "URL of the deployed service"
  value       = google_cloud_run_service.service.status[0].url
}

output "service_name" {
  description = "Name of the service"
  value       = google_cloud_run_service.service.name
}
```

## Calling Modules

### Local Module

```hcl
module "tiff_converter" {
  source = "./modules/cloud-run-service"

  service_name = "tiff-to-png-converter"
  project_id   = var.project_id
  region       = var.region
  image        = "gcr.io/${var.project_id}/tiff-converter:latest"
}
```

### Registry Module

```hcl
module "pubsub" {
  source  = "terraform-google-modules/pubsub/google"
  version = "~> 7.0"

  topic      = "invoice-uploaded"
  project_id = var.project_id
}
```

## Module Best Practices

| Practice | Why |
|----------|-----|
| No hardcoded values | Modules must be reusable |
| No provider config | Let root module configure |
| Expose all useful outputs | Consumers need flexibility |
| Use descriptive variable names | Self-documenting |
| Provide sensible defaults | Reduce required inputs |
| Pin module versions | Reproducible builds |

## Common Mistakes

| Wrong | Correct |
|-------|---------|
| Provider config in module | Let root module configure provider |
| Hardcoded values | Use variables with defaults |
| No version pins | Pin module versions |

## Related

- [Resources](./resources.md) | [Variables](./variables.md) | [Cloud Run Module](../patterns/cloud-run-module.md)
