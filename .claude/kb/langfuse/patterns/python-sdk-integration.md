# Python SDK Integration

> **Purpose**: Complete setup and basic instrumentation with Langfuse Python SDK
> **MCP Validated**: 2026-01-25

## When to Use

- Setting up Langfuse in a new Python project
- Adding observability to existing LLM applications
- Instrumenting Cloud Run functions or serverless workloads
- Debugging LLM call chains

## Implementation

```python
"""
Langfuse Python SDK Integration Pattern
For GenAI Invoice Processing Pipeline
"""
import os
from langfuse import get_client, Langfuse

# ============================================
# INITIALIZATION
# ============================================

# Option 1: Environment variables (recommended)
# Set in .env or Cloud Run environment:
# LANGFUSE_SECRET_KEY=sk-lf-...
# LANGFUSE_PUBLIC_KEY=pk-lf-...
# LANGFUSE_BASE_URL=https://cloud.langfuse.com

langfuse = get_client()

# Option 2: Explicit configuration
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    base_url=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
)

# Verify connection
if langfuse.auth_check():
    print("Langfuse connected successfully")


# ============================================
# BASIC TRACING
# ============================================

def process_invoice(image_bytes: bytes, user_id: str) -> dict:
    """Process invoice with full observability."""

    with langfuse.start_as_current_observation(
        as_type="span",
        name="process-invoice",
        user_id=user_id,
        metadata={"source": "cloud-run", "version": "1.0"}
    ) as trace:

        # Step 1: Preprocess
        with langfuse.start_as_current_observation(
            as_type="span",
            name="preprocess-image"
        ) as preprocess:
            processed = preprocess_image(image_bytes)
            preprocess.update(output={"size": len(processed)})

        # Step 2: LLM Extraction
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="extract-fields",
            model="gemini-1.5-pro",
            model_parameters={"temperature": 0.1}
        ) as generation:

            # Fetch managed prompt
            prompt = langfuse.get_prompt("invoice-extraction")
            compiled = prompt.compile(invoice_type="restaurant")

            generation.update(input=compiled)

            # Call LLM
            result = call_gemini(compiled, processed)

            generation.update(
                output=result.text,
                prompt=prompt,  # Link prompt version
                usage_details={
                    "input": result.usage.input_tokens,
                    "output": result.usage.output_tokens
                }
            )

            # Score extraction quality
            generation.score(
                name="extraction_confidence",
                value=result.confidence,
                data_type="NUMERIC"
            )

        # Step 3: Validate
        with langfuse.start_as_current_observation(
            as_type="span",
            name="validate-output"
        ) as validate:
            validated = validate_extraction(result.text)
            validate.update(output=validated)

        trace.update(output=validated)
        return validated


# ============================================
# FLUSH (Critical for serverless)
# ============================================

def cleanup():
    """Must call before process exits in serverless."""
    langfuse.flush()
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `LANGFUSE_SECRET_KEY` | Required | API secret key |
| `LANGFUSE_PUBLIC_KEY` | Required | API public key |
| `LANGFUSE_BASE_URL` | cloud.langfuse.com | Server endpoint |
| `sample_rate` | 1.0 | Trace sampling (0.0-1.0) |

## Example Usage

```python
# In Cloud Run function
def main(request):
    try:
        result = process_invoice(
            image_bytes=request.data,
            user_id=request.headers.get("X-User-ID", "anonymous")
        )
        return {"status": "success", "data": result}
    finally:
        cleanup()  # Always flush before exit
```

## See Also

- [Cloud Run Instrumentation](../patterns/cloud-run-instrumentation.md)
- [Traces and Spans](../concepts/traces-spans.md)
- [Generations](../concepts/generations.md)
