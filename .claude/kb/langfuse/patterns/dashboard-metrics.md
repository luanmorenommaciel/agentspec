# Dashboard Metrics

> **Purpose**: Key metrics and monitoring setup for LLM observability
> **MCP Validated**: 2026-01-25

## When to Use

- Setting up production monitoring dashboards
- Defining SLIs/SLOs for LLM applications
- Tracking project targets (cost, latency, quality)

## Implementation

```python
"""Dashboard Metrics Pattern - Key metrics for Invoice Processing Pipeline"""
from langfuse import get_client
from dataclasses import dataclass
import time

langfuse = get_client()

@dataclass
class ProjectTargets:
    cost_per_invoice: float = 0.003  # $0.003
    latency_p95_seconds: float = 3.0  # P95 < 3s
    accuracy_percent: float = 90.0   # 90% accuracy

TARGETS = ProjectTargets()

def record_pipeline_metrics(trace_id: str, latency_ms: float, cost_usd: float, accuracy: float, success: bool):
    """Record all key metrics for a single invoice processing."""
    langfuse.create_score(trace_id=trace_id, name="latency_ms",
        value=min(latency_ms / (TARGETS.latency_p95_seconds * 1000), 1.0),
        data_type="NUMERIC", comment=f"Latency: {latency_ms:.0f}ms")

    langfuse.create_score(trace_id=trace_id, name="cost_normalized",
        value=min(cost_usd / (TARGETS.cost_per_invoice * 3), 1.0),
        data_type="NUMERIC", comment=f"Cost: ${cost_usd:.4f}")

    langfuse.create_score(trace_id=trace_id, name="accuracy",
        value=accuracy, data_type="NUMERIC", comment=f"Accuracy: {accuracy * 100:.1f}%")

    langfuse.create_score(trace_id=trace_id, name="success", value=success, data_type="BOOLEAN")

    # SLO compliance flags
    langfuse.create_score(trace_id=trace_id, name="slo_latency_met",
        value=latency_ms <= TARGETS.latency_p95_seconds * 1000, data_type="BOOLEAN")
    langfuse.create_score(trace_id=trace_id, name="slo_cost_met",
        value=cost_usd <= TARGETS.cost_per_invoice, data_type="BOOLEAN")
    langfuse.create_score(trace_id=trace_id, name="slo_accuracy_met",
        value=accuracy >= TARGETS.accuracy_percent / 100, data_type="BOOLEAN")

def process_with_metrics(image_bytes: bytes, user_id: str) -> dict:
    """Full pipeline with comprehensive metrics."""
    start_time = time.time()

    with langfuse.start_as_current_observation(
        as_type="span", name="invoice-pipeline", user_id=user_id,
        metadata={"pipeline_version": "1.0"}
    ) as trace:
        try:
            with langfuse.start_as_current_observation(
                as_type="generation", name="extraction", model="gemini-1.5-pro"
            ) as gen:
                result = extract_invoice(image_bytes)
                usage = {"input": result.input_tokens, "output": result.output_tokens}
                gen.update(output=result.text, usage_details=usage)

            latency_ms = (time.time() - start_time) * 1000
            cost_usd = calculate_cost(usage, "gemini-1.5-pro")
            accuracy = evaluate_accuracy(result.text)

            record_pipeline_metrics(trace.trace_id, latency_ms, cost_usd, accuracy, True)
            trace.update(output=result.text, metadata={"latency_ms": latency_ms, "cost_usd": cost_usd})

            return {"result": result.text, "metrics": {"latency_ms": latency_ms, "cost_usd": cost_usd, "accuracy": accuracy}}

        except Exception as e:
            record_pipeline_metrics(trace.trace_id, (time.time()-start_time)*1000, 0, 0, False)
            raise
```

## Configuration

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Cost/invoice | $0.003 | > $0.005 |
| Latency P95 | 3s | > 5s |
| Accuracy | 90% | < 85% |

## Dashboard Queries

| View | Filter | Group By |
|------|--------|----------|
| Cost trend | score.name = "cost_normalized" | Day |
| Latency P95 | score.name = "latency_ms" | Hour |
| Accuracy | score.name = "accuracy" | Model |
| SLO compliance | score.name contains "slo_" | Week |

## See Also

- [Cost Tracking](../concepts/cost-tracking.md)
- [Scoring](../concepts/scoring.md)
