# Root Configuration

> **Purpose**: Central terragrunt.hcl that defines shared settings for all modules
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

The root configuration file sits at the top of your Terragrunt hierarchy. It defines
remote state, provider generation, and common settings inherited by all child modules.
This eliminates repetition across environments and modules.

## The Pattern

```hcl
# infrastructure/terragrunt.hcl (ROOT)

locals {
  # Parse environment from path
  env_vars = read_terragrunt_config(
    find_in_parent_folders("env.hcl", "empty.hcl")
  )

  project_id = local.env_vars.locals.project_id
  region     = local.env_vars.locals.region
  env        = local.env_vars.locals.environment
}

# Generate GCS backend configuration
generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  backend "gcs" {
    bucket = "${local.project_id}-tfstate"
    prefix = "${path_relative_to_include()}"
  }
}
EOF
}

# Generate provider configuration
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "google" {
  project = "${local.project_id}"
  region  = "${local.region}"
}

provider "google-beta" {
  project = "${local.project_id}"
  region  = "${local.region}"
}
EOF
}

# Default inputs for all modules
inputs = {
  project_id = local.project_id
  region     = local.region
  env        = local.env
}
```

## Quick Reference

| Component | Purpose | Generated File |
|-----------|---------|----------------|
| `generate "backend"` | State storage config | `backend.tf` |
| `generate "provider"` | GCP provider config | `provider.tf` |
| `inputs` | Common variables | N/A (passed to TF) |

## Environment File (env.hcl)

```hcl
# infrastructure/environments/dev/env.hcl

locals {
  environment = "dev"
  project_id  = "invoice-processing-dev"
  region      = "us-central1"

  # Environment-specific settings
  min_instances = 0
  max_instances = 2
}
```

## Common Mistakes

### Wrong

```hcl
# Hardcoding values in root
generate "backend" {
  contents = <<EOF
terraform {
  backend "gcs" {
    bucket = "my-state-bucket"  # Hardcoded!
    prefix = "terraform/state"   # Same for all modules!
  }
}
EOF
}
```

### Correct

```hcl
# Dynamic values from env.hcl
generate "backend" {
  contents = <<EOF
terraform {
  backend "gcs" {
    bucket = "${local.project_id}-tfstate"
    prefix = "${path_relative_to_include()}"
  }
}
EOF
}
```

## Related

- [terragrunt-blocks.md](terragrunt-blocks.md)
- [generate-blocks.md](generate-blocks.md)
- [state-bucket-per-env.md](../patterns/state-bucket-per-env.md)
