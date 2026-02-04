# Variables, Locals, and Outputs

> **Purpose**: Parameterize configurations for reusability
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Variables make Terraform configurations flexible and reusable. Input variables accept values from outside, local values simplify expressions, and outputs expose values to other configurations or users.

## Input Variables

### Declaration

```hcl
# variables.tf
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "enable_apis" {
  description = "Whether to enable required APIs"
  type        = bool
  default     = true
}
```

### Variable Types

| Type | Example | Use Case |
|------|---------|----------|
| `string` | `"us-central1"` | Single values |
| `number` | `100` | Counts, sizes |
| `bool` | `true` | Feature flags |
| `list(string)` | `["a", "b"]` | Multiple values |
| `set(string)` | `toset(["a", "b"])` | Unique values |
| `map(string)` | `{key = "value"}` | Key-value pairs |
| `object({...})` | Complex structures | Nested configs |

### Complex Variable Example

```hcl
variable "cloud_run_services" {
  description = "Cloud Run service configurations"
  type = list(object({
    name        = string
    image       = string
    memory      = optional(string, "512Mi")
    cpu         = optional(string, "1")
    min_scale   = optional(number, 0)
    max_scale   = optional(number, 10)
    env_vars    = optional(map(string), {})
  }))
}
```

## Setting Variable Values

### terraform.tfvars

```hcl
# terraform.tfvars
project_id  = "my-gcp-project"
region      = "us-central1"
environment = "prod"
```

### Command Line

```bash
terraform apply -var="project_id=my-project" -var-file="prod.tfvars"
```

## Local Values

Simplify complex expressions:

```hcl
# locals.tf
locals {
  # Computed values
  bucket_prefix = "${var.environment}-${var.project_id}"

  # Common tags
  common_labels = {
    environment = var.environment
    managed_by  = "terraform"
    project     = var.project_id
  }

  # Service list
  pipeline_stages = ["uploaded", "converted", "classified", "extracted"]
}

# Usage
resource "google_storage_bucket" "invoices" {
  name   = "${local.bucket_prefix}-invoices"
  labels = local.common_labels
}
```

## Outputs

```hcl
output "bucket_url" {
  description = "URL of the bucket"
  value       = google_storage_bucket.input.url
  sensitive   = false  # Set true to hide in logs
}
```

## Variable Precedence (Highest to Lowest)

1. Command line `-var` and `-var-file`
2. `*.auto.tfvars` files (alphabetical)
3. `terraform.tfvars`
4. Environment variables (`TF_VAR_name`)
5. Default values

## Related

- [Resources](./resources.md) | [Modules](./modules.md) | [Cloud Run Module](../patterns/cloud-run-module.md)
