# Event-Driven Pipeline Pattern

> **Purpose**: Decouple invoice processing stages using GCS, Pub/Sub, and Cloud Run
> **MCP Validated**: 2026-01-25

## When to Use

- Processing stages have different resource requirements (CPU, memory, timeout)
- Stages can fail independently and need retry logic
- You need observability at each pipeline step
- Workloads are bursty and benefit from scale-to-zero

## Implementation

```python
# Stage 1: TIFF Converter (triggered by GCS upload)
import functions_framework
from google.cloud import storage, pubsub_v1
from PIL import Image
import io
import json

@functions_framework.cloud_event
def convert_tiff_to_png(cloud_event):
    """Convert TIFF invoice to PNG and publish event."""
    data = cloud_event.data

    bucket_name = data["bucket"]
    file_name = data["name"]

    if not file_name.endswith(".tiff"):
        return

    # Download TIFF
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    tiff_bytes = blob.download_as_bytes()

    # Convert to PNG
    image = Image.open(io.BytesIO(tiff_bytes))
    png_buffer = io.BytesIO()
    image.save(png_buffer, format="PNG")

    # Upload PNG to processed bucket
    output_bucket = storage_client.bucket("invoices-processed")
    output_name = file_name.replace(".tiff", ".png")
    output_blob = output_bucket.blob(output_name)
    output_blob.upload_from_string(png_buffer.getvalue(), content_type="image/png")

    # Publish event for next stage
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path("my-project", "invoice-converted")

    message = json.dumps({
        "bucket": "invoices-processed",
        "name": output_name,
        "original": file_name
    }).encode()

    publisher.publish(topic_path, message)

    return f"Converted {file_name}"
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `trigger_bucket` | invoices-input | GCS bucket for uploads |
| `output_bucket` | invoices-processed | Destination for converted files |
| `pubsub_topic` | invoice-converted | Topic for next stage |
| `max_instances` | 50 | Scaling limit per stage |
| `timeout` | 300s | Per-request timeout |

## Example Usage

```bash
# Deploy TIFF converter with GCS trigger
gcloud run deploy tiff-converter \
  --source . \
  --function convert_tiff_to_png \
  --region us-central1 \
  --service-account tiff-converter@project.iam.gserviceaccount.com

# Create Eventarc trigger for GCS
gcloud eventarc triggers create tiff-upload-trigger \
  --location us-central1 \
  --destination-run-service tiff-converter \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=invoices-input" \
  --service-account eventarc@project.iam.gserviceaccount.com
```

## Pipeline Flow

```
[GCS: invoices-input]
        |
        v (Eventarc trigger)
[Cloud Run: tiff-converter]
        |
        v (Pub/Sub: invoice-converted)
[Cloud Run: invoice-classifier]
        |
        v (Pub/Sub: invoice-classified)
[Cloud Run: invoice-extractor]
        |
        v (Pub/Sub: invoice-extracted)
[Cloud Run: bigquery-writer]
        |
        v
[BigQuery: invoices.extracted_data]
```

## Error Handling

```python
# Dead-letter queue configuration (Terraform)
resource "google_pubsub_subscription" "with_dlq" {
  name  = "invoice-converted-sub"
  topic = google_pubsub_topic.invoice_converted.name

  push_config {
    push_endpoint = google_cloud_run_service.classifier.status[0].url
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq.id
    max_delivery_attempts = 5
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}
```

## See Also

- [Multi-Bucket Pipeline](../patterns/multi-bucket-pipeline.md)
- [Cloud Run](../concepts/cloud-run.md)
- [Pub/Sub](../concepts/pubsub.md)
