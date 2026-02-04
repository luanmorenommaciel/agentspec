# Model Comparison

> **Purpose**: A/B testing and analytics for comparing LLM models
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Langfuse enables model comparison by tracking metrics across different models, prompt versions, and configurations. Compare cost, latency, quality scores, and token usage to make data-driven decisions about model selection and prompt optimization.

## The Pattern

```python
from langfuse import get_client
import random

langfuse = get_client()

# A/B test between models
models = [
    {"name": "gemini-1.5-pro", "weight": 0.5},
    {"name": "gemini-1.5-flash", "weight": 0.5}
]

def select_model():
    r = random.random()
    cumulative = 0
    for model in models:
        cumulative += model["weight"]
        if r <= cumulative:
            return model["name"]
    return models[-1]["name"]

# Track with model metadata
selected_model = select_model()

with langfuse.start_as_current_observation(
    as_type="generation",
    name="invoice-extraction",
    model=selected_model,
    metadata={
        "experiment": "model-comparison-v1",
        "variant": selected_model
    }
) as generation:

    result = call_llm(model=selected_model)

    generation.update(
        output=result,
        usage_details={"input": 500, "output": 100}
    )

    # Score for comparison
    generation.score(
        name="extraction_accuracy",
        value=evaluate_accuracy(result),
        data_type="NUMERIC"
    )
```

## Quick Reference

| Metric | Compare By | Decision Factor |
|--------|------------|-----------------|
| Cost | Per request, per token | Budget constraints |
| Latency | P50, P95, P99 | User experience |
| Quality | Score averages | Accuracy requirements |
| Throughput | Requests/sec | Scale requirements |

## Comparison Dimensions

| Dimension | Filter/Group | Use Case |
|-----------|--------------|----------|
| `model` | Model name | Model A vs B |
| `prompt.version` | Prompt version | Prompt iteration |
| `metadata.experiment` | Custom tag | A/B experiments |
| `metadata.variant` | Custom tag | Feature flags |

## Common Mistakes

### Wrong

```python
# No experiment tracking - hard to compare later
with langfuse.start_as_current_observation(
    as_type="generation",
    model="gemini-1.5-pro"
) as gen:
    pass
```

### Correct

```python
# Tag for experiment analysis
with langfuse.start_as_current_observation(
    as_type="generation",
    model="gemini-1.5-pro",
    metadata={
        "experiment": "invoice-model-test",
        "variant": "pro"
    }
) as gen:
    gen.score(name="accuracy", value=0.95)
```

## Invoice Processing Comparison

| Model | Cost/Invoice | Latency P95 | Accuracy |
|-------|--------------|-------------|----------|
| gemini-1.5-pro | $0.003 | 2.5s | 95% |
| gemini-1.5-flash | $0.001 | 1.2s | 88% |
| gpt-4o | $0.004 | 3.0s | 94% |

## Analytics Queries

| Analysis | Langfuse Filter | Output |
|----------|-----------------|--------|
| Model cost | Group by model | Cost breakdown |
| Latency dist | Filter by model | P50/P95/P99 |
| Quality trend | Score over time | Trend chart |
| A/B results | Filter experiment | Variant comparison |

## Decision Matrix

| Priority | Choose |
|----------|--------|
| Cost-sensitive | gemini-1.5-flash |
| Accuracy-critical | gemini-1.5-pro |
| Balanced | Analyze A/B results |
| Low latency | gemini-1.5-flash |

## Related

- [Dashboard Metrics](../patterns/dashboard-metrics.md)
- [Cost Tracking](../concepts/cost-tracking.md)
- [Scoring](../concepts/scoring.md)
