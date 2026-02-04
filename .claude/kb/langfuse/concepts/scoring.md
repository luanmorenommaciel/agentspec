# Scoring

> **Purpose**: Quality feedback and evaluation metrics for LLM outputs
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Scores are flexible evaluation metrics that can be attached to traces, observations, or sessions. They support three data types: numeric (0.0-1.0), categorical (string labels), and boolean. Scores enable quality tracking through user feedback, automated evaluation, and LLM-as-Judge patterns.

## The Pattern

```python
from langfuse import get_client

langfuse = get_client()

# Method 1: Score within context
with langfuse.start_as_current_observation(
    as_type="generation",
    name="invoice-extraction",
    model="gemini-1.5-pro"
) as generation:

    result = extract_invoice(image)
    generation.update(output=result)

    # Score the current observation
    generation.score(
        name="extraction_accuracy",
        value=0.95,
        data_type="NUMERIC",
        comment="All fields extracted correctly"
    )

    # Score the entire trace
    generation.score_trace(
        name="overall_quality",
        value=0.90,
        data_type="NUMERIC"
    )

# Method 2: Score by trace ID (async/deferred)
langfuse.create_score(
    trace_id="trace-123",
    name="user_feedback",
    value=1,
    data_type="BOOLEAN",
    comment="User confirmed extraction was correct"
)
```

## Quick Reference

| Data Type | Values | Use Case |
|-----------|--------|----------|
| `NUMERIC` | 0.0 to 1.0 | Accuracy, confidence |
| `CATEGORICAL` | String labels | "correct", "incorrect", "partial" |
| `BOOLEAN` | True/False | Pass/fail, thumbs up/down |

## Score Methods

| Method | Scope | Context Required |
|--------|-------|------------------|
| `generation.score()` | Current observation | Yes |
| `generation.score_trace()` | Parent trace | Yes |
| `langfuse.create_score()` | Any trace/observation | No |
| `langfuse.score_current_span()` | Active context | Yes |

## Common Mistakes

### Wrong

```python
# Scoring after context closes - observation_id lost
with langfuse.start_as_current_observation(...) as gen:
    result = process()

# This won't link to the generation
gen.score(name="accuracy", value=0.9)  # Error: context closed
```

### Correct

```python
# Score inside context OR capture IDs for later
with langfuse.start_as_current_observation(...) as gen:
    result = process()
    trace_id = gen.trace_id  # Capture for later
    gen.score(name="accuracy", value=0.9)  # Works

# Or score later with captured ID
langfuse.create_score(
    trace_id=trace_id,
    name="user_feedback",
    value=True
)
```

## Invoice Processing Scores

| Score Name | Type | Target | Description |
|------------|------|--------|-------------|
| `extraction_accuracy` | NUMERIC | >= 0.90 | Field extraction correctness |
| `field_completeness` | NUMERIC | >= 0.95 | All required fields present |
| `user_verification` | BOOLEAN | True | Manual verification result |
| `confidence` | NUMERIC | >= 0.80 | Model confidence score |

## Analytics Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| Avg score | Mean over time | Quality trend |
| Score distribution | Histogram | Identify outliers |
| Cohen's Kappa | Agreement metric | Evaluator consistency |
| F1 Score | Precision/recall | Classification quality |

## Related

- [Quality Feedback Loops](../patterns/quality-feedback-loops.md)
- [Dashboard Metrics](../patterns/dashboard-metrics.md)
- [Traces and Spans](../concepts/traces-spans.md)
