# Terragrunt Blocks

> **Purpose**: Core HCL configuration blocks that make up a terragrunt.hcl file
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Terragrunt extends Terraform with special HCL blocks for DRY configurations,
dependency management, and code generation. Each block serves a specific purpose
in the configuration inheritance hierarchy.

## The Pattern

```hcl
# Complete terragrunt.hcl showing all major blocks

locals {
  # Local variables scoped to this file
  env_vars    = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  project_id  = local.env_vars.locals.project_id
  region      = local.env_vars.locals.region
}

include "root" {
  # Inherit from parent configuration
  path = find_in_parent_folders()
}

dependency "vpc" {
  # Declare dependency on another module
  config_path = "../vpc"

  mock_outputs = {
    network_name = "mock-vpc"
  }
}

terraform {
  # Module source and hooks
  source = "${get_terragrunt_dir()}/../../modules//cloud-run"
}

inputs = {
  # Variables passed to Terraform module
  project_id   = local.project_id
  region       = local.region
  network_name = dependency.vpc.outputs.network_name
}
```

## Quick Reference

| Block | Purpose | Required |
|-------|---------|----------|
| `locals` | Define local variables | No |
| `include` | Inherit parent config | Usually |
| `dependency` | Module execution order | For deps |
| `terraform` | Source and hooks | Yes |
| `inputs` | Pass vars to module | Usually |
| `generate` | Create dynamic files | Optional |
| `remote_state` | Auto-manage state | Optional |

## Block Details

### locals

```hcl
locals {
  # Read environment config from parent
  env_config = read_terragrunt_config(
    find_in_parent_folders("env.hcl")
  )

  # Extract specific values
  project_id = local.env_config.locals.project_id
  env        = local.env_config.locals.environment

  # Computed values
  resource_prefix = "${local.env}-invoice"
}
```

### include

```hcl
# Simple include
include "root" {
  path = find_in_parent_folders()
}

# Include with expose for accessing parent locals
include "env" {
  path   = find_in_parent_folders("env.hcl")
  expose = true
}

# Use exposed values
inputs = {
  project_id = include.env.locals.project_id
}
```

## Common Mistakes

### Wrong

```hcl
# Cannot access parent locals directly
include "root" {
  path = find_in_parent_folders()
}

inputs = {
  # ERROR: parent locals not accessible
  project_id = local.parent_project_id
}
```

### Correct

```hcl
# Use expose = true to access parent config
include "root" {
  path   = find_in_parent_folders()
  expose = true
}

inputs = {
  project_id = include.root.locals.project_id
}
```

## Related

- [root-configuration.md](root-configuration.md)
- [generate-blocks.md](generate-blocks.md)
- [dry-hierarchies.md](../patterns/dry-hierarchies.md)
