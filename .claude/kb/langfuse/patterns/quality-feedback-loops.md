# Quality Feedback Loops

> **Purpose**: Implement user feedback and automated evaluation for LLM quality
> **MCP Validated**: 2026-01-25

## When to Use

- Collecting user feedback on LLM outputs
- Implementing LLM-as-Judge automated evaluation
- Tracking accuracy against the 90% target

## Implementation

```python
"""Quality Feedback Loop Pattern - User feedback + automated scoring"""
from langfuse import get_client
import json

langfuse = get_client()

def record_user_feedback(trace_id: str, feedback_type: str, feedback_value, comment: str = None):
    """Record user feedback as score. Types: thumbs (bool), rating (1-5), correction (dict)"""
    if feedback_type == "thumbs":
        langfuse.create_score(trace_id=trace_id, name="user_thumbs",
            value=feedback_value, data_type="BOOLEAN", comment=comment)
    elif feedback_type == "rating":
        langfuse.create_score(trace_id=trace_id, name="user_rating",
            value=feedback_value / 5.0, data_type="NUMERIC", comment=comment)
    elif feedback_type == "correction":
        langfuse.create_score(trace_id=trace_id, name="user_correction",
            value="corrected", data_type="CATEGORICAL", comment=json.dumps(feedback_value))

def evaluate_extraction_quality(trace_id: str, extraction_result: dict, ground_truth: dict = None):
    """Automated quality evaluation using LLM-as-Judge."""
    with langfuse.start_as_current_observation(
        as_type="generation", name="llm-judge-evaluation",
        model="gemini-1.5-flash", metadata={"purpose": "evaluation"}
    ) as judge:
        eval_prompt = f"""Evaluate invoice extraction accuracy.
        Result: {json.dumps(extraction_result)}
        {"Ground Truth:" + json.dumps(ground_truth) if ground_truth else ""}
        Score 0-1: completeness, accuracy, format, overall. Return JSON."""

        result = call_gemini(eval_prompt)
        scores = json.loads(result.text)
        judge.update(input=eval_prompt, output=scores,
            usage_details={"input": result.usage.input_tokens, "output": result.usage.output_tokens})

        for dimension, value in scores.items():
            langfuse.create_score(trace_id=trace_id, name=f"judge_{dimension}",
                value=value, data_type="NUMERIC", comment="LLM-as-Judge evaluation")
        return scores

def calculate_field_accuracy(extraction: dict, ground_truth: dict) -> float:
    """Calculate field-level accuracy for invoice extraction."""
    fields = ["vendor_name", "invoice_date", "total_amount", "invoice_id"]
    return sum(1 for f in fields if extraction.get(f) == ground_truth.get(f)) / len(fields)

def process_with_quality_tracking(image_bytes: bytes, ground_truth: dict = None):
    """Full pipeline with quality tracking."""
    with langfuse.start_as_current_observation(as_type="span", name="quality-tracked-extraction") as trace:
        with langfuse.start_as_current_observation(
            as_type="generation", name="extraction", model="gemini-1.5-pro"
        ) as gen:
            result = extract_invoice(image_bytes)
            gen.update(output=result)

        if ground_truth:
            accuracy = calculate_field_accuracy(result, ground_truth)
            trace.score(name="field_accuracy", value=accuracy, data_type="NUMERIC")
            if accuracy < 0.90:
                trace.score(name="below_target", value=True, data_type="BOOLEAN",
                    comment="Below 90% accuracy target")

        judge_scores = evaluate_extraction_quality(trace.trace_id, result, ground_truth)
        trace.update(output={"result": result, "scores": judge_scores})
        return result, judge_scores
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Judge model | gemini-1.5-flash | Cheaper model for evaluation |
| Accuracy target | 0.90 | Project requirement |

## Example Usage

```python
record_user_feedback(trace_id="trace-123", feedback_type="thumbs", feedback_value=True)
scores = evaluate_extraction_quality("trace-123", {"vendor": "UberEats", "total": 42.50})
```

## See Also

- [Scoring](../concepts/scoring.md)
- [Dashboard Metrics](../patterns/dashboard-metrics.md)
