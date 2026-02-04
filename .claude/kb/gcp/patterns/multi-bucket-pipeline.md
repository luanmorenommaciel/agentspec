# Multi-Bucket Pipeline Pattern

> **Purpose**: Organize data by processing stage with separate GCS buckets
> **MCP Validated**: 2026-01-25

## When to Use

- Different retention policies per stage
- Stage-specific access control
- Clear audit trail of data flow
- Need to isolate failures (failed data in separate bucket)

## Implementation

```hcl
# Terraform: Multi-bucket infrastructure
locals {
  project_id = "my-invoice-project"
  region     = "us-central1"

  buckets = {
    input = {
      name            = "invoices-input"
      lifecycle_days  = 30
      storage_class   = "STANDARD"
    }
    processed = {
      name            = "invoices-processed"
      lifecycle_days  = 90
      storage_class   = "STANDARD"
    }
    archive = {
      name            = "invoices-archive"
      lifecycle_days  = 365
      storage_class   = "COLDLINE"
    }
    failed = {
      name            = "invoices-failed"
      lifecycle_days  = 90
      storage_class   = "STANDARD"
    }
  }
}

resource "google_storage_bucket" "pipeline" {
  for_each = local.buckets

  name          = "${local.project_id}-${each.value.name}"
  location      = local.region
  storage_class = each.value.storage_class

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = each.value.lifecycle_days
    }
    action {
      type = "Delete"
    }
  }

  versioning {
    enabled = each.key == "input"  # Version only input bucket
  }
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `input_bucket` | invoices-input | Raw TIFF uploads |
| `processed_bucket` | invoices-processed | Converted PNGs |
| `archive_bucket` | invoices-archive | Completed processing |
| `failed_bucket` | invoices-failed | Manual review queue |

## Example Usage

```python
# Move file between buckets based on processing result
from google.cloud import storage

def move_to_bucket(source_bucket: str, source_name: str,
                   dest_bucket: str, dest_name: str = None):
    """Move object between buckets (copy + delete)."""
    storage_client = storage.Client()

    src_bucket = storage_client.bucket(source_bucket)
    dst_bucket = storage_client.bucket(dest_bucket)
    src_blob = src_bucket.blob(source_name)

    # Copy to destination
    dst_name = dest_name or source_name
    src_bucket.copy_blob(src_blob, dst_bucket, dst_name)

    # Delete from source
    src_blob.delete()

    return f"gs://{dest_bucket}/{dst_name}"


def handle_processing_result(bucket: str, name: str, success: bool, error: str = None):
    """Route file based on processing outcome."""
    if success:
        return move_to_bucket(bucket, name, "invoices-archive")
    else:
        # Add error metadata before moving to failed bucket
        storage_client = storage.Client()
        blob = storage_client.bucket(bucket).blob(name)
        blob.metadata = {"error": error, "failed_at": datetime.utcnow().isoformat()}
        blob.patch()

        return move_to_bucket(bucket, name, "invoices-failed")
```

## Bucket Responsibilities

| Bucket | Trigger | Next Stage | Retention |
|--------|---------|------------|-----------|
| input | External upload | TIFF converter | 30 days |
| processed | TIFF converter output | Classifier, Extractor | 90 days |
| archive | Successful completion | None | 365 days |
| failed | Processing error | Manual review | 90 days |

## IAM Configuration

```hcl
# Least-privilege per stage
resource "google_storage_bucket_iam_member" "converter_read_input" {
  bucket = google_storage_bucket.pipeline["input"].name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.converter.email}"
}

resource "google_storage_bucket_iam_member" "converter_write_processed" {
  bucket = google_storage_bucket.pipeline["processed"].name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.converter.email}"
}

# Extractor only reads from processed
resource "google_storage_bucket_iam_member" "extractor_read_processed" {
  bucket = google_storage_bucket.pipeline["processed"].name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.extractor.email}"
}
```

## See Also

- [Event-Driven Pipeline](../patterns/event-driven-pipeline.md)
- [GCS](../concepts/gcs.md)
- [IAM](../concepts/iam.md)
