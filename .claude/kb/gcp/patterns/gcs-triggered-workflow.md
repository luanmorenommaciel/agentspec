# GCS-Triggered Workflow Pattern

> **Purpose**: Start serverless processing when files are uploaded to Cloud Storage
> **MCP Validated**: 2026-01-25

## When to Use

- Automatic processing when files arrive in a bucket
- Need to filter by file type, prefix, or suffix
- Want to decouple storage from processing logic
- Building file-based data pipelines

## Implementation

```python
# Cloud Run function triggered by GCS via Eventarc
import functions_framework
from cloudevents.http import CloudEvent
from google.cloud import storage
import os

@functions_framework.cloud_event
def handle_gcs_event(cloud_event: CloudEvent):
    """Process file uploaded to GCS."""
    data = cloud_event.data

    bucket_name = data["bucket"]
    file_name = data["name"]
    event_type = cloud_event["type"]

    # Filter by file extension
    if not file_name.lower().endswith((".tiff", ".tif")):
        print(f"Skipping non-TIFF file: {file_name}")
        return

    # Filter by prefix
    if file_name.startswith("temp/"):
        print(f"Skipping temp file: {file_name}")
        return

    print(f"Processing: gs://{bucket_name}/{file_name}")
    print(f"Event type: {event_type}")

    # Download and process
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    file_content = blob.download_as_bytes()

    # Process the file
    result = process_invoice(file_content, file_name)

    return {"status": "processed", "file": file_name}


def process_invoice(content: bytes, filename: str) -> dict:
    """Invoice processing logic."""
    # Convert, classify, extract...
    pass
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `bucket` | invoices-input | Watched bucket |
| `event_type` | finalized | Trigger on object creation |
| `service_region` | us-central1 | Cloud Run region |
| `trigger_region` | us-central1 | Eventarc trigger region |

## Example Usage

```bash
# Create Eventarc trigger for GCS events
gcloud eventarc triggers create invoice-upload-trigger \
  --location=us-central1 \
  --destination-run-service=tiff-converter \
  --destination-run-region=us-central1 \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=my-project-invoices-input" \
  --service-account=eventarc-trigger@my-project.iam.gserviceaccount.com

# List existing triggers
gcloud eventarc triggers list --location=us-central1

# Delete trigger
gcloud eventarc triggers delete invoice-upload-trigger --location=us-central1
```

## Terraform Configuration

```hcl
# Service account for Eventarc
resource "google_service_account" "eventarc" {
  account_id   = "eventarc-trigger"
  display_name = "Eventarc Trigger Service Account"
}

# Grant Eventarc permission to invoke Cloud Run
resource "google_cloud_run_service_iam_member" "eventarc_invoker" {
  location = google_cloud_run_service.converter.location
  service  = google_cloud_run_service.converter.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.eventarc.email}"
}

# Grant GCS permission to publish to Pub/Sub (for Eventarc)
resource "google_project_iam_member" "gcs_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${var.project_number}@gs-project-accounts.iam.gserviceaccount.com"
}

# Eventarc trigger
resource "google_eventarc_trigger" "gcs_trigger" {
  name     = "invoice-upload-trigger"
  location = "us-central1"

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.input.name
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_service.converter.name
      region  = "us-central1"
    }
  }

  service_account = google_service_account.eventarc.email
}
```

## Event Payload Structure

```json
{
  "bucket": "my-project-invoices-input",
  "name": "invoices/2026/01/invoice-001.tiff",
  "metageneration": "1",
  "timeCreated": "2026-01-25T10:30:00.000Z",
  "updated": "2026-01-25T10:30:00.000Z",
  "size": "1048576",
  "contentType": "image/tiff"
}
```

## Filtering Strategies

| Goal | Filter Method |
|------|---------------|
| Only TIFF files | Check `name.endswith(".tiff")` in code |
| Specific folder | Add `bucket` + prefix filtering |
| Ignore temp files | Check `not name.startswith("temp/")` |
| Multiple buckets | Create separate triggers per bucket |

## See Also

- [Event-Driven Pipeline](../patterns/event-driven-pipeline.md)
- [GCS](../concepts/gcs.md)
- [Cloud Run](../concepts/cloud-run.md)
