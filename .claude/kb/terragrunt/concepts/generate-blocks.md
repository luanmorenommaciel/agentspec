# Generate Blocks

> **Purpose**: Dynamically create Terraform files for backends, providers, and shared configs
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

The `generate` block creates files in the Terraform working directory before
Terraform runs. This is essential for injecting backend configuration, provider
settings, and shared code without duplicating across modules.

## The Pattern

```hcl
# Generate backend configuration
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
terraform "required_providers" {
  google = {
    source  = "hashicorp/google"
    version = "~> 5.0"
  }
}

provider "google" {
  project = "${local.project_id}"
  region  = "${local.region}"
}
EOF
}
```

## Quick Reference

| Attribute | Required | Description |
|-----------|----------|-------------|
| `path` | Yes | Output filename |
| `contents` | Yes | File contents |
| `if_exists` | No | Conflict handling |
| `comment_prefix` | No | Comment marker |
| `disable_signature` | No | Skip Terragrunt comment |

## if_exists Options

| Value | Behavior |
|-------|----------|
| `overwrite_terragrunt` | Overwrite only Terragrunt-generated files |
| `overwrite` | Always overwrite |
| `skip` | Skip if file exists |
| `error` | Error if file exists |

## Generate vs remote_state

```hcl
# Option 1: generate (manual bucket management)
generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  backend "gcs" {
    bucket = "my-state-bucket"
    prefix = "env/${path_relative_to_include()}"
  }
}
EOF
}

# Option 2: remote_state (auto bucket creation)
remote_state {
  backend = "gcs"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    bucket   = "my-state-bucket"
    prefix   = "env/${path_relative_to_include()}"
    project  = local.project_id
    location = local.region
  }
}
```

## Common Mistakes

### Wrong

```hcl
# Using both for the same purpose
generate "backend" { ... }
remote_state { ... }  # Conflict!
```

### Correct

```hcl
# Choose ONE approach
# Use generate when bucket already exists
# Use remote_state when you want auto-creation
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
```

## Related

- [root-configuration.md](root-configuration.md)
- [state-bucket-per-env.md](../patterns/state-bucket-per-env.md)
- [terragrunt-blocks.md](terragrunt-blocks.md)
