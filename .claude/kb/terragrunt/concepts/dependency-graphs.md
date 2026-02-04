# Dependency Graphs

> **Purpose**: Define execution order between Terraform modules and pass outputs
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Terragrunt uses `dependency` blocks to understand the provisioning order between
modules. It builds a directed acyclic graph (DAG) and ensures modules are applied
in the correct order. Dependencies also enable passing outputs between modules.

## The Pattern

```hcl
# environments/dev/cloud-run/terragrunt.hcl

include "root" {
  path = find_in_parent_folders()
}

# Declare dependencies
dependency "vpc" {
  config_path = "../vpc"
}

dependency "pubsub" {
  config_path = "../pubsub"
}

dependency "iam" {
  config_path = "../iam"
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//cloud-run"
}

# Use dependency outputs as inputs
inputs = {
  network_name      = dependency.vpc.outputs.network_name
  subnetwork_name   = dependency.vpc.outputs.subnetwork_name
  topic_id          = dependency.pubsub.outputs.topic_id
  service_account   = dependency.iam.outputs.service_account_email
}
```

## Quick Reference

| Attribute | Required | Description |
|-----------|----------|-------------|
| `config_path` | Yes | Path to dependency module |
| `mock_outputs` | No | Fake outputs for plan |
| `mock_outputs_allowed_terraform_commands` | No | Commands that can use mocks |
| `mock_outputs_merge_strategy_with_state` | No | How to merge with real state |

## Mock Outputs

```hcl
dependency "vpc" {
  config_path = "../vpc"

  # Enable planning without applying vpc first
  mock_outputs = {
    network_name    = "mock-network"
    subnetwork_name = "mock-subnet"
    network_id      = "mock-network-id"
  }

  # Only allow mocks for these commands
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}
```

## Run-All Commands

```bash
terragrunt run-all apply    # Apply in dependency order
terragrunt run-all plan     # Plan all modules
terragrunt run-all destroy  # Destroy in reverse order
terragrunt graph-dependencies  # Visualize DAG
```

## Common Mistakes

### Wrong

```hcl
# Circular dependency
# Module A depends on B, B depends on A
dependency "module_b" {
  config_path = "../module-b"  # module-b also depends on module-a!
}
```

### Correct

```hcl
# Linear dependency chain
# VPC -> IAM -> Pub/Sub -> Cloud Run
dependency "pubsub" {
  config_path = "../pubsub"
}
# pubsub depends on iam
# iam depends on vpc
# No cycles
```

## Accessing Nested Outputs

```hcl
dependency "vpc" {
  config_path = "../vpc"
}

inputs = {
  # Access map output
  subnet_cidr = dependency.vpc.outputs.subnets["us-central1"]

  # Access list output
  first_zone = dependency.vpc.outputs.zones[0]
}
```

## Related

- [dependency-management.md](../patterns/dependency-management.md)
- [terragrunt-blocks.md](terragrunt-blocks.md)
- [hooks.md](hooks.md)
