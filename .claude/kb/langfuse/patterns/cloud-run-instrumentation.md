# Cloud Run Function Instrumentation

> **Purpose**: Complete tracing setup for GCP Cloud Run functions with Langfuse
> **MCP Validated**: 2026-01-25

## When to Use

- Deploying LLM-powered Cloud Run functions
- Event-driven processing (Pub/Sub triggered)
- HTTP-triggered serverless endpoints
- Invoice processing pipeline functions

## Implementation

```python
"""
Cloud Run Function with Langfuse Instrumentation
GCS -> Pub/Sub -> Cloud Run -> Gemini -> BigQuery
"""
import os
import json
import functions_framework
from langfuse import get_client

# Initialize client (uses environment variables)
langfuse = get_client()


@functions_framework.cloud_event
def process_invoice_event(cloud_event):
    """
    Pub/Sub triggered invoice processing with full observability.
    Triggered when new invoice uploaded to GCS.
    """
    # Extract event data
    data = json.loads(cloud_event.data["message"]["data"])
    bucket = data.get("bucket")
    file_name = data.get("name")
    trace_id = data.get("trace_id")  # For distributed tracing

    try:
        with langfuse.start_as_current_observation(
            as_type="span",
            name="cloud-run-invoice-processor",
            trace_id=trace_id,  # Link to upstream trace
            metadata={
                "bucket": bucket,
                "file": file_name,
                "event_id": cloud_event["id"],
                "function": os.getenv("K_SERVICE", "unknown")
            }
        ) as trace:

            # Download from GCS
            with langfuse.start_as_current_observation(
                as_type="span",
                name="gcs-download"
            ) as download:
                image_bytes = download_from_gcs(bucket, file_name)
                download.update(output={"bytes": len(image_bytes)})

            # Extract with LLM
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="gemini-extraction",
                model="gemini-1.5-pro",
                model_parameters={"temperature": 0.1, "max_tokens": 1024}
            ) as generation:

                prompt = langfuse.get_prompt("invoice-extraction")
                result = call_gemini_vision(prompt.compile(), image_bytes)

                generation.update(
                    output=result.text,
                    prompt=prompt,
                    usage_details={
                        "input": result.usage.input_tokens,
                        "output": result.usage.output_tokens
                    }
                )

                # Score extraction quality
                generation.score(
                    name="extraction_accuracy",
                    value=calculate_confidence(result),
                    data_type="NUMERIC"
                )

            # Write to BigQuery
            with langfuse.start_as_current_observation(
                as_type="span",
                name="bigquery-write"
            ) as bq_span:
                parsed = json.loads(result.text)
                write_to_bigquery(parsed)
                bq_span.update(output={"rows_written": 1})

            trace.update(output={"status": "success", "invoice_id": parsed.get("invoice_id")})

    except Exception as e:
        # Log error to trace
        langfuse.create_score(
            trace_id=trace_id,
            name="error",
            value="error",
            data_type="CATEGORICAL",
            comment=str(e)
        )
        raise

    finally:
        # CRITICAL: Flush before Cloud Run instance terminates
        langfuse.flush()


@functions_framework.http
def process_invoice_http(request):
    """HTTP-triggered variant for synchronous processing."""

    user_id = request.headers.get("X-User-ID", "anonymous")
    request_id = request.headers.get("X-Request-ID")

    try:
        with langfuse.start_as_current_observation(
            as_type="span",
            name="http-invoice-processor",
            user_id=user_id,
            session_id=request.headers.get("X-Session-ID"),
            metadata={"request_id": request_id}
        ) as trace:

            # Process...
            result = process_invoice(request.data)
            trace.update(output=result)

            return json.dumps(result), 200

    finally:
        langfuse.flush()
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `LANGFUSE_SECRET_KEY` | Required | Set in Cloud Run secrets |
| `LANGFUSE_PUBLIC_KEY` | Required | Set in Cloud Run env |
| `LANGFUSE_BASE_URL` | cloud.langfuse.com | EU or US region |

## Example Usage

```yaml
# cloudbuild.yaml or terraform
env_vars:
  - name: LANGFUSE_PUBLIC_KEY
    value: pk-lf-...
secrets:
  - name: LANGFUSE_SECRET_KEY
    secret: langfuse-secret-key
    version: latest
```

## See Also

- [Python SDK Integration](../patterns/python-sdk-integration.md)
- [Trace Linking](../patterns/trace-linking.md)
- [Traces and Spans](../concepts/traces-spans.md)
