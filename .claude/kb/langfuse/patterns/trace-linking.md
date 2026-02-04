# Trace Linking

> **Purpose**: Distributed tracing across services and functions
> **MCP Validated**: 2026-01-25

## When to Use

- Tracking requests across multiple Cloud Run functions
- Linking Pub/Sub messages to traces
- Debugging distributed workflows

## Implementation

```python
"""Trace Linking Pattern - Distributed tracing across services"""
import json
import uuid
from langfuse import get_client

langfuse = get_client()

def generate_trace_id() -> str:
    return f"trace-{uuid.uuid4().hex[:16]}"

def publish_with_trace(bucket: str, file_name: str, trace_id: str = None):
    """Publish Pub/Sub message with trace context."""
    from google.cloud import pubsub_v1
    trace_id = trace_id or generate_trace_id()

    with langfuse.start_as_current_observation(
        as_type="span", name="gcs-upload-trigger",
        trace_id=trace_id, metadata={"bucket": bucket, "file": file_name}
    ) as span:
        message = {
            "bucket": bucket, "name": file_name,
            "trace_id": trace_id, "parent_span_id": span.id
        }
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path("project-id", "invoice-topic")
        future = publisher.publish(topic_path, json.dumps(message).encode("utf-8"))
        span.update(output={"message_id": future.result()})

def process_with_trace_context(cloud_event):
    """Process Pub/Sub message, continuing the trace."""
    data = json.loads(cloud_event.data["message"]["data"])
    trace_id = data.get("trace_id")
    parent_span_id = data.get("parent_span_id")

    with langfuse.start_as_current_observation(
        as_type="span", name="pubsub-processor",
        trace_id=trace_id, parent_observation_id=parent_span_id,
        metadata={"event_id": cloud_event["id"]}
    ) as span:
        result = process_invoice(data["bucket"], data["name"])
        span.update(output=result)
        if needs_further_processing(result):
            call_downstream_service(result, trace_id=trace_id, parent_span_id=span.id)
    langfuse.flush()

def call_downstream_service(data: dict, trace_id: str, parent_span_id: str):
    """Call downstream HTTP service with trace context."""
    import requests
    with langfuse.start_as_current_observation(
        as_type="span", name="downstream-call", trace_id=trace_id
    ) as span:
        response = requests.post(
            "https://validation-service.run.app/validate", json=data,
            headers={"X-Trace-ID": trace_id, "X-Parent-Span-ID": span.id}
        )
        span.update(output={"status": response.status_code})
        return response.json()

def receive_from_upstream(request):
    """Receive HTTP request and continue trace."""
    trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()
    parent_span_id = request.headers.get("X-Parent-Span-ID")
    with langfuse.start_as_current_observation(
        as_type="span", name="validation-service",
        trace_id=trace_id, parent_observation_id=parent_span_id
    ) as span:
        result = validate(request.json)
        span.update(output=result)
        return result

def get_trace_url(trace_id: str) -> str:
    return f"https://cloud.langfuse.com/project/your-project-id/traces/{trace_id}"
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `X-Trace-ID` | Header | HTTP trace ID propagation |
| `X-Parent-Span-ID` | Header | Parent span for linking |
| `trace_id` | Message attr | Pub/Sub propagation |

## Example Usage

```python
publish_with_trace(bucket="invoices-bucket", file_name="invoice-001.tiff")
trace_url = get_trace_url("trace-abc123")
```

## See Also

- [Cloud Run Instrumentation](../patterns/cloud-run-instrumentation.md)
- [Traces and Spans](../concepts/traces-spans.md)
