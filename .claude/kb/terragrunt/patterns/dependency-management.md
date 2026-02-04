# Dependency Management Pattern

> **Purpose**: Orchestrate module execution order and pass outputs between modules
> **MCP Validated**: 2026-01-25

## When to Use

- Module needs outputs from another module
- Must enforce creation order (VPC before compute)
- Running `terragrunt run-all` across modules
- Need to mock dependencies for planning

## Implementation

```hcl
# infrastructure/environments/dev/vpc/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//vpc"
}

inputs = {
  network_name = "invoice-network"
  subnet_cidr  = "10.0.0.0/24"
}
```

```hcl
# infrastructure/environments/dev/iam/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

dependency "vpc" {
  config_path = "../vpc"
  mock_outputs = {
    network_name = "mock-network"
  }
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//iam"
}

inputs = {
  network_name = dependency.vpc.outputs.network_name
}
```

```hcl
# infrastructure/environments/dev/pubsub/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

dependency "iam" {
  config_path = "../iam"
  mock_outputs = {
    pubsub_service_account = "mock-sa@project.iam.gserviceaccount.com"
  }
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//pubsub"
}

inputs = {
  topic_name        = "invoice-uploads"
  service_account   = dependency.iam.outputs.pubsub_service_account
}
```

```hcl
# infrastructure/environments/dev/cloud-run/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

# Multiple dependencies
dependency "vpc" {
  config_path = "../vpc"
  mock_outputs = {
    network_name    = "mock-network"
    subnetwork_name = "mock-subnet"
  }
}

dependency "pubsub" {
  config_path = "../pubsub"
  mock_outputs = {
    topic_id        = "projects/mock/topics/mock"
    subscription_id = "projects/mock/subscriptions/mock"
  }
}

dependency "iam" {
  config_path = "../iam"
  mock_outputs = {
    cloud_run_service_account = "mock-sa@project.iam.gserviceaccount.com"
  }
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//cloud-run"
}

inputs = {
  service_name      = "invoice-processor"
  network_name      = dependency.vpc.outputs.network_name
  subnetwork_name   = dependency.vpc.outputs.subnetwork_name
  topic_id          = dependency.pubsub.outputs.topic_id
  subscription_id   = dependency.pubsub.outputs.subscription_id
  service_account   = dependency.iam.outputs.cloud_run_service_account
}
```

## Configuration

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `config_path` | Path to dependency | `"../vpc"` |
| `mock_outputs` | Fake outputs for plan | `{ network = "mock" }` |
| `mock_outputs_allowed_terraform_commands` | When to use mocks | `["validate", "plan"]` |
| `skip_outputs` | Don't fetch outputs | `true` (for destroy) |

## Dependency Graph

```bash
# Visualize dependencies
terragrunt graph-dependencies

# Output:
# digraph {
#   "cloud-run" -> "vpc"
#   "cloud-run" -> "pubsub"
#   "cloud-run" -> "iam"
#   "pubsub" -> "iam"
#   "iam" -> "vpc"
# }

# Execution order for apply:
# 1. vpc
# 2. iam (depends on vpc)
# 3. pubsub (depends on iam)
# 4. cloud-run (depends on vpc, pubsub, iam)
```

## Example Usage

```bash
# Apply all in correct order
terragrunt run-all apply

# Destroy in reverse order
terragrunt run-all destroy

# Apply single module (dependencies auto-fetched)
cd cloud-run && terragrunt apply
```

## See Also

- [dependency-graphs.md](../concepts/dependency-graphs.md)
- [multi-environment-config.md](multi-environment-config.md)
- [terragrunt-blocks.md](../concepts/terragrunt-blocks.md)
