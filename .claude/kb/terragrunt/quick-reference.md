# Terragrunt Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-01-25

## Core Blocks

| Block | Purpose | Example |
|-------|---------|---------|
| `include` | Inherit parent config | `include "root" { path = find_in_parent_folders() }` |
| `dependency` | Define module order | `dependency "vpc" { config_path = "../vpc" }` |
| `inputs` | Pass vars to Terraform | `inputs = { project_id = local.project_id }` |
| `locals` | Define local variables | `locals { env = "dev" }` |
| `generate` | Create dynamic files | `generate "backend" { ... }` |
| `remote_state` | Configure state backend | `remote_state { backend = "gcs" ... }` |
| `terraform` | Module source + hooks | `terraform { source = "../modules//vpc" }` |

## Built-in Functions

| Function | Returns | Use Case |
|----------|---------|----------|
| `find_in_parent_folders()` | Path to root config | Include inheritance |
| `path_relative_to_include()` | Relative path | State key generation |
| `get_terragrunt_dir()` | Current config dir | Hook working dirs |
| `get_env("VAR", "default")` | Env var value | Dynamic configuration |
| `read_terragrunt_config()` | Parsed config | Cross-file references |

## Include Merge Strategies

| Strategy | Behavior | Use When |
|----------|----------|----------|
| `shallow` | Child overrides parent | Simple inheritance |
| `deep` | Recursive merge | Complex nested configs |
| `no_merge` | No merging | Reference only |

## Run-All Commands

| Command | Action |
|---------|--------|
| `terragrunt run-all init` | Initialize all modules |
| `terragrunt run-all plan` | Plan all modules (respects deps) |
| `terragrunt run-all apply` | Apply in dependency order |
| `terragrunt run-all destroy` | Destroy in reverse order |
| `terragrunt graph-dependencies` | Visualize module graph |

## Hook Commands

| Command | When |
|---------|------|
| `init-from-module` | After go-getter downloads |
| `init` | After terraform init |
| `plan` | During terraform plan |
| `apply` | During terraform apply |
| `destroy` | During terraform destroy |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Auto-create state bucket | `remote_state` block |
| Manual bucket management | `generate` block |
| Share vars across envs | Root `locals` + include |
| Module-to-module data | `dependency` + outputs |

## Common Pitfalls

| Do Not | Do Instead |
|--------|------------|
| Use both `remote_state` and `generate` for backend | Pick one approach |
| Access parent locals directly | Use `expose = true` in include |
| Nest include blocks | Flatten to single level |
| Mix state in one bucket | Use `path_relative_to_include()` for keys |

## Related Documentation

| Topic | Path |
|-------|------|
| Block Details | `concepts/terragrunt-blocks.md` |
| Root Setup | `concepts/root-configuration.md` |
| Full Index | `index.md` |
