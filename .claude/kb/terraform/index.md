# Terraform for GCP Knowledge Base

> **Purpose**: Infrastructure as Code reference for GCP serverless architecture
> **MCP Validated**: 2026-01-25

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/resources.md](concepts/resources.md) | Resources and data sources fundamentals |
| [concepts/modules.md](concepts/modules.md) | Module structure, inputs, outputs |
| [concepts/providers.md](concepts/providers.md) | GCP provider configuration |
| [concepts/state.md](concepts/state.md) | State management and remote backends |
| [concepts/variables.md](concepts/variables.md) | Variables, locals, and outputs |
| [concepts/workspaces.md](concepts/workspaces.md) | Environment isolation with workspaces |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/cloud-run-module.md](patterns/cloud-run-module.md) | Cloud Run service with Pub/Sub trigger |
| [patterns/pubsub-module.md](patterns/pubsub-module.md) | Topics, subscriptions, dead-letter queues |
| [patterns/gcs-module.md](patterns/gcs-module.md) | Buckets, lifecycle rules, notifications |
| [patterns/bigquery-module.md](patterns/bigquery-module.md) | Datasets, tables, schemas |
| [patterns/iam-module.md](patterns/iam-module.md) | Service accounts and IAM bindings |
| [patterns/remote-state.md](patterns/remote-state.md) | GCS backend for state management |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables for commands and configs

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Declarative IaC** | Define desired state, Terraform reconciles |
| **Modules** | Reusable, composable infrastructure packages |
| **State** | Source of truth for managed resources |
| **Providers** | Plugins for cloud platform APIs |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/resources.md, concepts/variables.md |
| **Intermediate** | concepts/modules.md, patterns/remote-state.md |
| **Advanced** | patterns/iam-module.md, concepts/workspaces.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| infra-agent | patterns/*.md | Provision GCP resources |
| python-developer | patterns/cloud-run-module.md | Deploy Cloud Run services |

---

## Project Context

This KB supports the GenAI Invoice Processing Pipeline infrastructure:

| Component | Terraform Module |
|-----------|------------------|
| 4 Cloud Run services | patterns/cloud-run-module.md |
| 4 Pub/Sub topics | patterns/pubsub-module.md |
| 4 GCS buckets | patterns/gcs-module.md |
| 1 BigQuery dataset | patterns/bigquery-module.md |
| Service accounts | patterns/iam-module.md |
| State management | patterns/remote-state.md |

---

## External Resources

- [Terraform GCP Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Google Terraform Modules](https://github.com/terraform-google-modules)
- [GCP Terraform Best Practices](https://cloud.google.com/docs/terraform/best-practices)
