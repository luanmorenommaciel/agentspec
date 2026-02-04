# Hooks

> **Purpose**: Execute custom commands before, after, or on error of Terraform operations
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Hooks in Terragrunt allow custom actions around Terraform commands. Use them for
tasks like secret injection, validation, cleanup, or notifications. Hooks run
in the context of the Terraform working directory.

## The Pattern

```hcl
terraform {
  source = "${get_terragrunt_dir()}/../../../modules//cloud-run"

  # Run before terraform apply/plan
  before_hook "validate_config" {
    commands = ["apply", "plan"]
    execute  = ["./scripts/validate.sh"]
  }

  # Run after terraform apply/plan
  after_hook "notify_slack" {
    commands     = ["apply"]
    execute      = ["./scripts/notify.sh", "success"]
    run_on_error = false
  }

  # Run only on error
  error_hook "alert_on_failure" {
    commands = ["apply", "plan"]
    execute  = ["./scripts/notify.sh", "failure"]
  }
}
```

## Quick Reference

| Hook Type | When It Runs | Use Case |
|-----------|--------------|----------|
| `before_hook` | Before Terraform command | Validation, secrets |
| `after_hook` | After Terraform command | Cleanup, notification |
| `error_hook` | On Terraform error | Alerting, rollback |

## Hook Attributes

| Attribute | Required | Description |
|-----------|----------|-------------|
| `commands` | Yes | Which TF commands trigger hook |
| `execute` | Yes | Command to run as array |
| `run_on_error` | No | Run after_hook on error (default: false) |
| `working_dir` | No | Override working directory |
| `suppress_stdout` | No | Hide command output |

## Special Commands

| Command | Trigger Point |
|---------|--------------|
| `init-from-module` | After go-getter downloads source |
| `init` | After terraform init |
| `plan` | During terraform plan |
| `apply` | During terraform apply |
| `destroy` | During terraform destroy |

## Real-World Examples

### Secret Injection

```hcl
terraform {
  before_hook "inject_secrets" {
    commands = ["plan", "apply"]
    execute  = [
      "bash", "-c",
      "gcloud secrets versions access latest --secret=db-password > .secrets"
    ]
  }

  after_hook "cleanup_secrets" {
    commands     = ["plan", "apply"]
    execute      = ["rm", "-f", ".secrets"]
    run_on_error = true
  }
}
```

### Format Check

```hcl
terraform {
  before_hook "terraform_fmt" {
    commands = ["plan", "apply"]
    execute  = ["terraform", "fmt", "-check"]
  }
}
```

## Common Mistakes

### Wrong

```hcl
# Hook won't run - init-from-module only runs when source is downloaded
terraform {
  # No source defined

  after_hook "post_init" {
    commands = ["init-from-module"]  # Never triggers!
    execute  = ["echo", "done"]
  }
}
```

### Correct

```hcl
terraform {
  source = "../../../modules//vpc"

  after_hook "post_init" {
    commands = ["init-from-module"]  # Triggers after source download
    execute  = ["echo", "Module downloaded"]
  }
}
```

## Related

- [terragrunt-blocks.md](terragrunt-blocks.md)
- [dependency-graphs.md](dependency-graphs.md)
- [environment-promotion.md](../patterns/environment-promotion.md)
