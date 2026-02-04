# State Bucket Per Environment Pattern

> **Purpose**: Isolate Terraform state between environments for security and safety
> **MCP Validated**: 2026-01-25

## When to Use

- Need complete environment isolation
- Different teams manage dev vs prod
- Compliance requires state separation
- Want to prevent accidental cross-env changes

## Implementation

```hcl
# infrastructure/terragrunt.hcl (ROOT)
locals {
  env_config = read_terragrunt_config(
    find_in_parent_folders("env.hcl")
  )
  project_id = local.env_config.locals.project_id
  region     = local.env_config.locals.region
  env        = local.env_config.locals.environment
}

# Each environment gets its own bucket
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

```hcl
# infrastructure/environments/dev/env.hcl
locals {
  environment = "dev"
  project_id  = "invoice-processing-dev"
  region      = "us-central1"
}
# State bucket: invoice-processing-dev-tfstate
```

```hcl
# infrastructure/environments/prod/env.hcl
locals {
  environment = "prod"
  project_id  = "invoice-processing-prod"
  region      = "us-central1"
}
# State bucket: invoice-processing-prod-tfstate
```

## Alternative: Single Bucket with Prefixes

```hcl
# For simpler setups with fewer compliance requirements
generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  backend "gcs" {
    bucket = "company-terraform-state"
    prefix = "${local.env}/${path_relative_to_include()}"
  }
}
EOF
}
# State paths:
# - dev/cloud-run/default.tfstate
# - prod/cloud-run/default.tfstate
```

## Auto-Create Buckets with remote_state

```hcl
# infrastructure/terragrunt.hcl
remote_state {
  backend = "gcs"

  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }

  config = {
    bucket   = "${local.project_id}-tfstate"
    prefix   = path_relative_to_include()
    project  = local.project_id
    location = local.region

    # Auto-enable features
    enable_bucket_policy_only = true
  }
}
```

## Configuration

| Setting | Dev | Prod | Purpose |
|---------|-----|------|---------|
| `bucket` | `*-dev-tfstate` | `*-prod-tfstate` | Isolation |
| `prefix` | `module/path` | `module/path` | Organization |
| `project` | `*-dev` | `*-prod` | Billing separation |

## State Structure

```text
# Dev bucket: invoice-processing-dev-tfstate
environments/dev/vpc/default.tfstate
environments/dev/iam/default.tfstate
environments/dev/pubsub/default.tfstate
environments/dev/cloud-run/default.tfstate
environments/dev/bigquery/default.tfstate

# Prod bucket: invoice-processing-prod-tfstate
environments/prod/vpc/default.tfstate
environments/prod/iam/default.tfstate
environments/prod/pubsub/default.tfstate
environments/prod/cloud-run/default.tfstate
environments/prod/bigquery/default.tfstate
```

## Bucket Setup (Manual)

```bash
# Create state buckets (one-time setup)
for ENV in dev prod; do
  PROJECT="invoice-processing-${ENV}"
  gsutil mb -p ${PROJECT} -l us-central1 gs://${PROJECT}-tfstate
  gsutil versioning set on gs://${PROJECT}-tfstate
done
```

## Example Usage

```bash
# Verify state isolation
cd infrastructure/environments/dev/cloud-run
terragrunt state list
# Output: resources in dev state only

cd infrastructure/environments/prod/cloud-run
terragrunt state list
# Output: resources in prod state only (completely separate)
```

## See Also

- [multi-environment-config.md](multi-environment-config.md)
- [root-configuration.md](../concepts/root-configuration.md)
- [generate-blocks.md](../concepts/generate-blocks.md)
