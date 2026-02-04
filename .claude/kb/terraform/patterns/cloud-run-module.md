# Cloud Run Module Pattern

> **Purpose**: Reusable module for deploying Cloud Run services with Pub/Sub triggers
> **MCP Validated**: 2026-01-25

## When to Use

- Deploy containerized services on Cloud Run
- Need consistent configuration across multiple services
- Services triggered by Pub/Sub or HTTP
- Require IAM and secret management integration

## Module Structure

```text
modules/cloud-run/
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
└── iam.tf
```

## Implementation

### Key Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `service_name` | string | required | Cloud Run service name |
| `project_id` | string | required | GCP project ID |
| `image` | string | required | Container image URL |
| `service_account_email` | string | required | SA for the service |
| `memory` | string | `"512Mi"` | Memory allocation |
| `timeout` | number | `300` | Request timeout (seconds) |
| `concurrency` | number | `80` | Max requests per instance |
| `min_instances` | number | `0` | Min instances (cold start) |
| `max_instances` | number | `100` | Max instances (cost) |

### main.tf

```hcl
resource "google_cloud_run_v2_service" "service" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    service_account = var.service_account_email
    timeout         = "${var.timeout}s"

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.image

      resources {
        limits = {
          memory = var.memory
          cpu    = var.cpu
        }
      }

      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.value.name
          value_source {
            secret_key_ref {
              secret  = env.value.secret_name
              version = env.value.version
            }
          }
        }
      }
    }

    max_instance_request_concurrency = var.concurrency
  }
}
```

### iam.tf

```hcl
resource "google_cloud_run_v2_service_iam_member" "invoker" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
```

### outputs.tf

```hcl
output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.service.uri
}

output "service_name" {
  description = "Name of the service"
  value       = google_cloud_run_v2_service.service.name
}

output "service_id" {
  description = "Full resource ID"
  value       = google_cloud_run_v2_service.service.id
}
```

## Example Usage

```hcl
module "tiff_converter" {
  source = "./modules/cloud-run"

  service_name          = "tiff-to-png-converter"
  project_id            = var.project_id
  region                = var.region
  image                 = "gcr.io/${var.project_id}/tiff-converter:v1"
  service_account_email = google_service_account.converter.email

  memory        = "1Gi"
  timeout       = 300
  concurrency   = 1   # CPU-intensive
  min_instances = 0
  max_instances = 50

  env_vars = {
    OUTPUT_BUCKET = google_storage_bucket.processed.name
    PUBSUB_TOPIC  = google_pubsub_topic.converted.name
  }

  secrets = [
    {
      name        = "LANGFUSE_SECRET_KEY"
      secret_name = google_secret_manager_secret.langfuse.secret_id
    }
  ]
}
```

## Related

- [Pub/Sub Module](./pubsub-module.md)
- [IAM Module](./iam-module.md)
- [Cloud Run Concept](../concepts/modules.md)
