# Cloud Run

> **Purpose**: Fully managed serverless platform for containerized applications
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Cloud Run is a managed compute platform that runs stateless containers invocable via HTTP requests or events. It abstracts infrastructure, auto-scales from zero to thousands of instances, and charges only for resources used during request processing.

## The Pattern

```python
# Cloud Run function triggered by Pub/Sub
import functions_framework
from cloudevents.http import CloudEvent

@functions_framework.cloud_event
def process_invoice(cloud_event: CloudEvent):
    """Triggered by Pub/Sub message."""
    import base64
    import json

    # Decode Pub/Sub message
    data = base64.b64decode(cloud_event.data["message"]["data"])
    message = json.loads(data)

    bucket = message["bucket"]
    file_name = message["name"]

    # Process the invoice
    result = extract_invoice_data(bucket, file_name)

    return result
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| HTTP request | HTTP response | Request timeout up to 60 min |
| CloudEvent | Processing result | Pub/Sub, GCS triggers via Eventarc |
| Scheduled trigger | Job completion | Via Cloud Scheduler |

## Key Configuration

| Setting | Purpose | Invoice Pipeline |
|---------|---------|------------------|
| `--min-instances` | Cold start prevention | 1 for critical functions |
| `--max-instances` | Cost control | 10-100 based on load |
| `--concurrency` | Requests per instance | 1 for CPU-heavy LLM calls |
| `--memory` | Container memory | 1Gi for image processing |
| `--timeout` | Max request duration | 300s for LLM extraction |

## Common Mistakes

### Wrong

```bash
# Using default service account (overly permissive)
gcloud run deploy my-service --image gcr.io/project/image
```

### Correct

```bash
# Using dedicated service account with least privilege
gcloud run deploy my-service \
  --image gcr.io/project/image \
  --service-account invoice-processor@project.iam.gserviceaccount.com \
  --min-instances 1 \
  --max-instances 50 \
  --concurrency 1 \
  --memory 1Gi \
  --timeout 300
```

## Deployment Options

| Method | Use Case |
|--------|----------|
| Source-based | Python, Node.js, Go - automatic containerization |
| Container-based | Custom runtimes, specific dependencies |
| Terraform | Infrastructure as code deployment |

## Scaling Behavior

1. **Scale to zero**: No cost when idle (cold start on first request)
2. **Rapid scale-out**: New instances spawn in seconds
3. **Concurrency**: Multiple requests per instance (set to 1 for LLM)
4. **Min instances**: Keep warm for latency-sensitive workloads

## Related

- [Event-Driven Pipeline](../patterns/event-driven-pipeline.md)
- [Cloud Run Scaling](../patterns/cloud-run-scaling.md)
- [Pub/Sub](../concepts/pubsub.md)
