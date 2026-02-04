# BigQuery Module Pattern

> **Purpose**: Reusable module for datasets, tables, and schema management
> **MCP Validated**: 2026-01-25

## When to Use

- Create BigQuery datasets with consistent configuration
- Define tables with JSON schemas
- Manage partitioning and clustering
- Set up access controls per dataset

## Module Structure

```text
modules/bigquery/
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
└── schemas/
    └── invoice_extracted.json
```

## Implementation

### Key Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `dataset_id` | string | required | BigQuery dataset ID |
| `project_id` | string | required | GCP project ID |
| `location` | string | `"US"` | Dataset location |
| `tables` | list(object) | `[]` | Tables with schemas |
| `access` | list(object) | `[]` | Access controls |

### main.tf

```hcl
resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = var.dataset_id
  project                     = var.project_id
  location                    = var.location
  description                 = var.description
  default_table_expiration_ms = var.default_table_expiration_ms
  delete_contents_on_destroy  = var.delete_contents_on_destroy
  labels                      = var.labels

  dynamic "access" {
    for_each = var.access
    content {
      role           = access.value.role
      user_by_email  = access.value.user_by_email
      group_by_email = access.value.group_by_email
      special_group  = access.value.special_group
    }
  }
}

resource "google_bigquery_table" "tables" {
  for_each = { for table in var.tables : table.table_id => table }

  dataset_id          = google_bigquery_dataset.dataset.dataset_id
  table_id            = each.value.table_id
  project             = var.project_id
  description         = each.value.description
  deletion_protection = true
  labels              = var.labels

  schema = file(each.value.schema_file)

  clustering = length(each.value.clustering) > 0 ? each.value.clustering : null

  dynamic "time_partitioning" {
    for_each = each.value.time_partitioning != null ? [each.value.time_partitioning] : []
    content {
      type  = time_partitioning.value.type
      field = time_partitioning.value.field
    }
  }
}
```

### outputs.tf

```hcl
output "dataset_id" {
  description = "Dataset ID"
  value       = google_bigquery_dataset.dataset.dataset_id
}

output "dataset_self_link" {
  description = "Self link of the dataset"
  value       = google_bigquery_dataset.dataset.self_link
}

output "table_ids" {
  description = "Map of table IDs"
  value       = { for k, v in google_bigquery_table.tables : k => v.table_id }
}

output "full_table_ids" {
  description = "Fully qualified table IDs"
  value = {
    for k, v in google_bigquery_table.tables :
    k => "${var.project_id}.${var.dataset_id}.${v.table_id}"
  }
}
```

## Example Usage

```hcl
module "invoice_intelligence" {
  source = "./modules/bigquery"

  dataset_id  = "invoice_intelligence"
  project_id  = var.project_id
  location    = "US"
  description = "Invoice extraction and analytics data"

  tables = [
    {
      table_id    = "extracted_invoices"
      description = "Extracted invoice data from LLM"
      schema_file = "${path.module}/schemas/invoice_extracted.json"
      clustering  = ["vendor_name", "invoice_date"]
      time_partitioning = {
        type  = "DAY"
        field = "extracted_at"
      }
    },
    {
      table_id    = "processing_logs"
      description = "Invoice processing audit logs"
      schema_file = "${path.module}/schemas/processing_log.json"
      time_partitioning = {
        type = "DAY"
      }
    }
  ]

  access = [
    {
      role          = "WRITER"
      user_by_email = google_service_account.bq_writer.email
    }
  ]

  labels = local.common_labels
}
```

## Related

- [IAM Module](./iam-module.md)
- [GCS Module](./gcs-module.md)
- [Resources Concept](../concepts/resources.md)
