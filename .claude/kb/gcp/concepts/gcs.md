# Google Cloud Storage (GCS)

> **Purpose**: Object storage service with event triggers for serverless pipelines
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Google Cloud Storage is a unified object storage service for unstructured data. In serverless pipelines, GCS serves as both storage and event source. Object changes trigger Cloud Run functions via Eventarc, enabling reactive data processing.

## The Pattern

```python
# Read from GCS in Cloud Run function
from google.cloud import storage

def download_invoice(bucket_name: str, blob_name: str) -> bytes:
    """Download invoice file from GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    return blob.download_as_bytes()

def upload_processed(bucket_name: str, blob_name: str, data: bytes):
    """Upload processed file to GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_string(
        data,
        content_type="image/png"
    )
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| File upload | `finalized` event | Triggers via Eventarc |
| Object delete | `deleted` event | Cleanup workflows |
| Metadata update | `metadataUpdated` event | Tag-based processing |

## Invoice Pipeline Buckets

| Bucket | Purpose | Lifecycle |
|--------|---------|-----------|
| `invoices-input` | Raw TIFF uploads | 30-day retention |
| `invoices-processed` | Converted PNGs | 90-day retention |
| `invoices-archive` | Completed invoices | Cold storage after 30 days |
| `invoices-failed` | Failed processing | Manual review |

## Event Types

| Event | When Fired | Use Case |
|-------|------------|----------|
| `finalized` | Object created/overwritten | Start processing |
| `deleted` | Permanent deletion | Cleanup dependent data |
| `archived` | Version archived | Versioned bucket only |
| `metadataUpdated` | Metadata changed | Status updates |

## Common Mistakes

### Wrong

```python
# No content type, no error handling
blob.upload_from_string(data)
```

### Correct

```python
from google.cloud.storage import Blob

def upload_with_metadata(bucket_name: str, blob_name: str, data: bytes):
    """Upload with proper metadata and error handling."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Set metadata for tracking
    blob.metadata = {
        "processed_at": datetime.utcnow().isoformat(),
        "pipeline_version": "1.0"
    }

    blob.upload_from_string(
        data,
        content_type="image/png",
        timeout=300
    )
```

## Lifecycle Rules

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 30, "matchesPrefix": ["archive/"]}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
```

## Storage Classes

| Class | Use Case | Invoice Pipeline |
|-------|----------|------------------|
| Standard | Frequent access | Input, processed |
| Nearline | Monthly access | Archive |
| Coldline | Quarterly access | Long-term archive |
| Archive | Yearly access | Compliance retention |

## Related

- [GCS-Triggered Workflow](../patterns/gcs-triggered-workflow.md)
- [Multi-Bucket Pipeline](../patterns/multi-bucket-pipeline.md)
- [Cloud Run](../concepts/cloud-run.md)
