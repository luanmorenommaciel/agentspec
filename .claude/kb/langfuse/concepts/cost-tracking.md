# Cost Tracking

> **Purpose**: Monitor and analyze LLM costs through token usage and pricing
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Langfuse automatically calculates costs for generations at ingestion time when usage data and pricing information are available. Built-in support covers OpenAI, Anthropic, and Google models. For custom models, you can configure pricing via the UI or API.

## The Pattern

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="generation",
    name="invoice-extraction",
    model="gemini-1.5-pro",
    input="Extract invoice fields from this image..."
) as generation:

    response = call_llm()

    # Option 1: Auto-calculation (supported models)
    generation.update(
        output=response.text,
        usage_details={
            "input": response.input_tokens,
            "output": response.output_tokens
        }
    )

    # Option 2: Manual cost override
    generation.update(
        output=response.text,
        usage_details={
            "input": 500,
            "output": 100
        },
        cost_details={
            "input": 0.0005,   # $0.001 per 1K tokens
            "output": 0.0003,  # $0.003 per 1K tokens
            "total": 0.0008
        }
    )
```

## Quick Reference

| Method | Description | Precedence |
|--------|-------------|------------|
| Auto-calculation | Langfuse infers from model name | Default |
| Manual `cost_details` | Explicitly set costs | Overrides auto |
| Custom model config | Define pricing in settings | Applied to new |

## Usage Detail Fields

| Field | Description | Example |
|-------|-------------|---------|
| `input` | Input/prompt tokens | `500` |
| `output` | Output/completion tokens | `100` |
| `total` | Sum of all tokens | `600` |
| `cache_read_input_tokens` | Cached input tokens | `200` |

## Common Mistakes

### Wrong

```python
# Using non-standard model name - no auto cost
generation.update(
    model="my-fine-tuned-gpt4"  # Not recognized
)
```

### Correct

```python
# Use standard model names OR configure custom
generation.update(
    model="gpt-4o"  # Recognized, auto-cost applied
)

# Or for custom models, configure in Langfuse UI:
# Project Settings > Models > Add Model
# - match_pattern: "my-fine-tuned-.*"
# - input_price: 0.001
# - output_price: 0.003
```

## Invoice Processing Cost Example

| Metric | Value | Notes |
|--------|-------|-------|
| Target cost | $0.003/invoice | Project requirement |
| Avg input tokens | 1,500 | Image + prompt |
| Avg output tokens | 200 | JSON response |
| Gemini 1.5 Pro | ~$0.002 | Within budget |

## Metrics Available

| Metric | Aggregation | Use Case |
|--------|-------------|----------|
| Total cost | Sum | Budget tracking |
| Cost by model | Group by | Model comparison |
| Cost by user | Group by | User analytics |
| Cost over time | Time series | Trend analysis |

## Related

- [Generations](../concepts/generations.md)
- [Cost Alerting](../patterns/cost-alerting.md)
- [Dashboard Metrics](../patterns/dashboard-metrics.md)
