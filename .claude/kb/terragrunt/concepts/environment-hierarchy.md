# Environment Hierarchy

> **Purpose**: Folder structure pattern for managing multiple environments with Terragrunt
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Terragrunt uses a hierarchical folder structure where configuration files at each level
inherit from parent directories. This enables DRY configurations where common settings
live in parent files and environment-specific overrides live in child files.

## The Pattern

```text
infrastructure/
|-- terragrunt.hcl              # ROOT: backend, providers, common inputs
|-- modules/                    # Reusable Terraform modules
|   |-- cloud-run/
|   |-- pubsub/
|   |-- gcs/
|   |-- bigquery/
|   |-- iam/
|-- environments/
    |-- _env/                   # Shared environment configs (optional)
    |   |-- cloud-run.hcl
    |   |-- pubsub.hcl
    |-- dev/
    |   |-- env.hcl             # Dev-specific variables
    |   |-- cloud-run/
    |   |   |-- terragrunt.hcl
    |   |-- pubsub/
    |   |   |-- terragrunt.hcl
    |   |-- gcs/
    |       |-- terragrunt.hcl
    |-- prod/
        |-- env.hcl             # Prod-specific variables
        |-- cloud-run/
        |   |-- terragrunt.hcl
        |-- pubsub/
        |   |-- terragrunt.hcl
        |-- gcs/
            |-- terragrunt.hcl
```

## Configuration Inheritance

### Root Level (infrastructure/terragrunt.hcl)

```hcl
# Defines backend, providers, common inputs
# All child modules inherit this
generate "backend" { ... }
generate "provider" { ... }
```

### Environment Level (environments/dev/env.hcl)

```hcl
# Environment-specific variables
locals {
  environment = "dev"
  project_id  = "invoice-processing-dev"
  region      = "us-central1"

  # Resource sizing for dev
  cloud_run_min_instances = 0
  cloud_run_max_instances = 2
  cloud_run_memory        = "512Mi"
}
```

### Module Level (environments/dev/cloud-run/terragrunt.hcl)

```hcl
# Inherits root + env, adds module-specific config
include "root" {
  path = find_in_parent_folders()
}

include "env" {
  path   = find_in_parent_folders("env.hcl")
  expose = true
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//cloud-run"
}

inputs = {
  service_name  = "invoice-processor"
  min_instances = include.env.locals.cloud_run_min_instances
  max_instances = include.env.locals.cloud_run_max_instances
  memory        = include.env.locals.cloud_run_memory
}
```

## Quick Reference

| Level | File | Contains |
|-------|------|----------|
| Root | `terragrunt.hcl` | Backend, providers, shared inputs |
| _env | `_env/*.hcl` | Shared module configs (optional) |
| Environment | `env.hcl` | Project, region, sizing |
| Module | `*/terragrunt.hcl` | Source, dependencies, inputs |

## Common Mistakes

### Wrong

```text
# Flat structure - lots of duplication
infrastructure/
|-- dev-cloud-run/terragrunt.hcl
|-- dev-pubsub/terragrunt.hcl
|-- prod-cloud-run/terragrunt.hcl
|-- prod-pubsub/terragrunt.hcl
```

### Correct

```text
# Hierarchical - DRY configuration
infrastructure/
|-- terragrunt.hcl
|-- environments/
    |-- dev/
    |   |-- env.hcl
    |   |-- cloud-run/terragrunt.hcl
    |-- prod/
        |-- env.hcl
        |-- cloud-run/terragrunt.hcl
```

## Related

- [dry-hierarchies.md](../patterns/dry-hierarchies.md)
- [multi-environment-config.md](../patterns/multi-environment-config.md)
- [root-configuration.md](root-configuration.md)
