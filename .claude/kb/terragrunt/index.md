# Terragrunt Knowledge Base

> **Purpose**: Terraform wrapper for multi-environment orchestration, DRY configurations, and dependency management
> **MCP Validated**: 2026-01-25

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/terragrunt-blocks.md](concepts/terragrunt-blocks.md) | Core HCL blocks: include, dependency, inputs, locals |
| [concepts/root-configuration.md](concepts/root-configuration.md) | Root terragrunt.hcl and provider setup |
| [concepts/environment-hierarchy.md](concepts/environment-hierarchy.md) | Folder structure for multi-env setups |
| [concepts/generate-blocks.md](concepts/generate-blocks.md) | Dynamic file generation for backends |
| [concepts/dependency-graphs.md](concepts/dependency-graphs.md) | Module dependencies and execution order |
| [concepts/hooks.md](concepts/hooks.md) | before_hook, after_hook, error_hook |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/multi-environment-config.md](patterns/multi-environment-config.md) | Dev/prod with different GCP projects |
| [patterns/dry-hierarchies.md](patterns/dry-hierarchies.md) | Root to env to module inheritance |
| [patterns/dependency-management.md](patterns/dependency-management.md) | Cross-module output passing |
| [patterns/state-bucket-per-env.md](patterns/state-bucket-per-env.md) | Isolated state per environment |
| [patterns/environment-promotion.md](patterns/environment-promotion.md) | Promoting changes dev to prod |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/gcp-project-structure.yaml](specs/gcp-project-structure.yaml) | Standard GCP Terragrunt layout |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **include** | Merge parent config into child (shallow/deep) |
| **dependency** | Define execution order between modules |
| **generate** | Create files dynamically (backend, providers) |
| **inputs** | Pass variables to Terraform modules |
| **run-all** | Execute across multiple modules respecting deps |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/terragrunt-blocks.md, concepts/root-configuration.md |
| **Intermediate** | patterns/multi-environment-config.md, patterns/dry-hierarchies.md |
| **Advanced** | patterns/dependency-management.md, concepts/hooks.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| terraform-developer | patterns/multi-environment-config.md | Setup new environment |
| infrastructure-agent | patterns/dependency-management.md | Module orchestration |

---

## Project Context

This KB supports the GenAI Invoice Processing Pipeline infrastructure:
- Multi-environment GCP deployment (dev/prod)
- Module dependencies: VPC -> Pub/Sub -> Cloud Run -> BigQuery
- Remote state in GCS with per-environment buckets
- DRY configuration across cloud-run, pubsub, gcs, bigquery, iam modules
