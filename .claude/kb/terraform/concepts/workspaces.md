# Workspaces

> **Purpose**: Environment isolation within a single configuration
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Workspaces allow you to manage multiple distinct sets of infrastructure resources from a single configuration. Each workspace has its own state file, enabling environment separation (dev, staging, prod).

## Workspace Commands

| Command | Purpose |
|---------|---------|
| `terraform workspace list` | Show all workspaces |
| `terraform workspace show` | Show current workspace |
| `terraform workspace new <name>` | Create workspace |
| `terraform workspace select <name>` | Switch workspace |
| `terraform workspace delete <name>` | Delete workspace |

## Basic Usage

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch to workspace
terraform workspace select prod

# Apply (uses prod state)
terraform apply -var-file="prod.tfvars"
```

## Using Workspace in Configuration

```hcl
# Access current workspace
locals {
  environment = terraform.workspace

  # Environment-specific settings
  config = {
    dev = {
      min_instances = 0
      max_instances = 2
      machine_type  = "f1-micro"
    }
    staging = {
      min_instances = 1
      max_instances = 5
      machine_type  = "e2-small"
    }
    prod = {
      min_instances = 2
      max_instances = 100
      machine_type  = "e2-medium"
    }
  }

  current_config = local.config[local.environment]
}

resource "google_cloud_run_service" "api" {
  name = "invoice-api-${terraform.workspace}"

  template {
    spec {
      container_concurrency = 80
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = local.current_config.min_instances
        "autoscaling.knative.dev/maxScale" = local.current_config.max_instances
      }
    }
  }
}
```

## State File Organization

With GCS backend, workspaces create separate state files:

```hcl
terraform {
  backend "gcs" {
    bucket = "tf-state-myproject"
    prefix = "invoice-pipeline"
  }
}
```

Results in:
```text
gs://tf-state-myproject/
├── invoice-pipeline/
│   ├── default.tfstate
│   ├── dev.tfstate
│   ├── staging.tfstate
│   └── prod.tfstate
```

## Workspaces vs Directory Structure

### When to Use Workspaces

- Same infrastructure, different environments
- Quick environment switching
- Shared configuration logic

### When to Use Directories

- Different infrastructure per environment
- Different provider configurations
- Independent state management

## Workspace-Aware Naming

```hcl
resource "google_storage_bucket" "data" {
  name = "invoice-data-${var.project_id}-${terraform.workspace}"
}
```

## Best Practices

| Practice | Why |
|----------|-----|
| Name workspaces like environments | Clarity (dev, staging, prod) |
| Use workspace-aware naming | Prevent collisions |
| Consider directories for complex cases | Better isolation |

## Related

- [State](./state.md) | [Remote State](../patterns/remote-state.md) | [Providers](./providers.md)
