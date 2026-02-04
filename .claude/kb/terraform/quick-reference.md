# Terraform Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-01-25

## Essential Commands

| Command | Purpose |
|---------|---------|
| `terraform init` | Initialize, download providers |
| `terraform plan` | Preview changes |
| `terraform apply` | Apply changes to infrastructure |
| `terraform destroy` | Remove all managed resources |
| `terraform fmt` | Format configuration files |
| `terraform validate` | Check configuration syntax |
| `terraform output` | Display output values |
| `terraform state list` | List resources |

## File Structure

| File | Purpose |
|------|---------|
| `main.tf` | Primary resource definitions |
| `variables.tf` | Input variable declarations |
| `outputs.tf` | Output value declarations |
| `providers.tf` | Provider configuration |
| `versions.tf` | Required provider versions |
| `backend.tf` | Remote state configuration |
| `locals.tf` | Local values |

## GCP Provider Configuration

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}
```

## Variable Types

| Type | Example |
|------|---------|
| `string` | `"us-central1"` |
| `number` | `100` |
| `bool` | `true` |
| `list(string)` | `["a", "b"]` |
| `map(string)` | `{key = "value"}` |
| `object({})` | Complex structures |

## Common Resource Arguments

| Argument | Purpose |
|----------|---------|
| `depends_on` | Explicit dependency |
| `count` | Create multiple instances |
| `for_each` | Iterate over map/set |
| `lifecycle` | Control resource behavior |
| `provider` | Select specific provider |

## Lifecycle Rules

```hcl
lifecycle {
  create_before_destroy = true
  prevent_destroy       = true
  ignore_changes        = [tags]
}
```

## GCS Backend (Remote State)

```hcl
terraform {
  backend "gcs" {
    bucket = "tf-state-bucket"
    prefix = "env/prod"
  }
}
```

## Decision Matrix

| Need | Choose |
|------|--------|
| Multiple environments | Workspaces or directory structure |
| Reusable components | Modules |
| Secrets in state | Encrypt GCS bucket |
| Team collaboration | Remote state with locking |
| Resource count varies | `count` or `for_each` |

## Common Pitfalls

| Avoid | Do Instead |
|-------|------------|
| Hardcoded values | Use variables |
| State in git | Use GCS backend |
| No version pins | Pin provider versions |

## Related: [index.md](index.md)
