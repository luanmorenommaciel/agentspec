# Generations

> **Purpose**: Specialized observation type for tracking LLM calls with token usage and costs
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

A generation is a specialized observation type designed for LLM calls. It extends the basic span with additional fields for model name, parameters, token counts (input/output/cached), and cost calculations. Langfuse automatically tracks tokens and costs for supported models.

## The Pattern

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="generation",
    name="invoice-extraction",
    model="gemini-1.5-pro",
    model_parameters={
        "temperature": 0.1,
        "max_tokens": 1024
    },
    input=[
        {"role": "system", "content": "Extract invoice fields..."},
        {"role": "user", "content": "Invoice image attached"}
    ]
) as generation:

    # Call your LLM
    response = call_gemini_api(prompt)

    # Update with output and usage
    generation.update(
        output=response.text,
        usage_details={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
            "total": response.usage.total_tokens
        }
    )
```

## Quick Reference

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model identifier (e.g., "gemini-1.5-pro") |
| `model_parameters` | dict | Temperature, max_tokens, etc. |
| `input` | list/string | Prompt or message array |
| `output` | string/dict | Model response |
| `usage_details` | dict | Token counts by type |
| `cost_details` | dict | Calculated costs |

## Token Usage Types

| Type | Description |
|------|-------------|
| `input` | Prompt/input tokens |
| `output` | Completion/output tokens |
| `total` | Sum of all tokens |
| `cache_read_input_tokens` | Cached prompt tokens |
| `audio_tokens` | Audio input tokens |
| `image_tokens` | Image input tokens |

## Common Mistakes

### Wrong

```python
# Missing model name - no auto cost calculation
with langfuse.start_as_current_observation(
    as_type="generation",
    name="llm-call"
) as gen:
    gen.update(output="response")
```

### Correct

```python
# Include model for automatic cost tracking
with langfuse.start_as_current_observation(
    as_type="generation",
    name="llm-call",
    model="gemini-1.5-pro"  # Required for auto-cost
) as gen:
    gen.update(
        output="response",
        usage_details={"input": 100, "output": 50}
    )
```

## Auto-Supported Models

| Provider | Models | Tokenizer |
|----------|--------|-----------|
| OpenAI | gpt-4o, gpt-4, gpt-3.5-turbo | o200k_base, cl100k_base |
| Anthropic | claude-3.5-sonnet, claude-3-opus | Anthropic tokenizer |
| Google | gemini-1.5-pro, gemini-1.5-flash | Google tokenizer |

## Related

- [Cost Tracking](../concepts/cost-tracking.md)
- [Traces and Spans](../concepts/traces-spans.md)
- [Python SDK Integration](../patterns/python-sdk-integration.md)
