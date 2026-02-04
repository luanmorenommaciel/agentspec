# Cost Alerting

> **Purpose**: Monitor LLM costs and alert on threshold breaches
> **MCP Validated**: 2026-01-25

## When to Use

- Monitoring production LLM spend
- Alerting when per-request cost exceeds budget
- Tracking cost trends over time
- Implementing cost guardrails

## Implementation

```python
"""
Cost Alerting Pattern
Monitor and alert on LLM costs with $0.003/invoice target
"""
import os
from langfuse import get_client
from dataclasses import dataclass

langfuse = get_client()


@dataclass
class CostThresholds:
    """Cost thresholds for invoice processing."""
    per_invoice_target: float = 0.003  # $0.003 per invoice
    per_invoice_warning: float = 0.005  # $0.005 warning level
    per_invoice_critical: float = 0.010  # $0.010 critical level
    daily_budget: float = 100.0  # $100/day
    monthly_budget: float = 3000.0  # $3000/month


THRESHOLDS = CostThresholds()


# ============================================
# COST CALCULATION
# ============================================

def calculate_generation_cost(usage_details: dict, model: str) -> float:
    """
    Calculate cost based on token usage.
    Prices per 1K tokens (as of 2026).
    """
    pricing = {
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "claude-3.5-sonnet": {"input": 0.003, "output": 0.015}
    }

    if model not in pricing:
        return 0.0

    rates = pricing[model]
    input_cost = (usage_details.get("input", 0) / 1000) * rates["input"]
    output_cost = (usage_details.get("output", 0) / 1000) * rates["output"]

    return input_cost + output_cost


# ============================================
# COST MONITORING
# ============================================

def process_with_cost_monitoring(image_bytes: bytes) -> dict:
    """Process invoice with cost monitoring and alerting."""

    with langfuse.start_as_current_observation(
        as_type="span",
        name="cost-monitored-extraction"
    ) as trace:

        with langfuse.start_as_current_observation(
            as_type="generation",
            name="extraction",
            model="gemini-1.5-pro"
        ) as generation:

            result = call_gemini(image_bytes)

            usage = {
                "input": result.usage.input_tokens,
                "output": result.usage.output_tokens
            }

            generation.update(
                output=result.text,
                usage_details=usage
            )

            # Calculate and check cost
            cost = calculate_generation_cost(usage, "gemini-1.5-pro")

            # Score for cost tracking
            generation.score(
                name="request_cost",
                value=min(cost / THRESHOLDS.per_invoice_critical, 1.0),
                data_type="NUMERIC",
                comment=f"Cost: ${cost:.6f}"
            )

            # Alert on threshold breach
            if cost > THRESHOLDS.per_invoice_critical:
                generation.score(
                    name="cost_alert",
                    value="critical",
                    data_type="CATEGORICAL",
                    comment=f"Cost ${cost:.4f} exceeds critical ${THRESHOLDS.per_invoice_critical}"
                )
                alert_cost_breach("critical", cost, trace.trace_id)

            elif cost > THRESHOLDS.per_invoice_warning:
                generation.score(
                    name="cost_alert",
                    value="warning",
                    data_type="CATEGORICAL",
                    comment=f"Cost ${cost:.4f} exceeds warning ${THRESHOLDS.per_invoice_warning}"
                )
                alert_cost_breach("warning", cost, trace.trace_id)

            elif cost > THRESHOLDS.per_invoice_target:
                generation.score(
                    name="cost_alert",
                    value="above_target",
                    data_type="CATEGORICAL",
                    comment=f"Cost ${cost:.4f} above target ${THRESHOLDS.per_invoice_target}"
                )

        trace.update(
            output={"result": result.text, "cost": cost},
            metadata={"cost_usd": cost}
        )

        return {"result": result.text, "cost": cost}


def alert_cost_breach(level: str, cost: float, trace_id: str):
    """Send alert for cost threshold breach."""
    # Integration with Cloud Monitoring, PagerDuty, Slack, etc.
    print(f"COST ALERT [{level.upper()}]: ${cost:.4f} - Trace: {trace_id}")


# ============================================
# COST OPTIMIZATION
# ============================================

def select_model_by_budget(remaining_budget: float) -> str:
    """Select model based on remaining budget."""
    if remaining_budget > 50:
        return "gemini-1.5-pro"  # Best quality
    elif remaining_budget > 10:
        return "gemini-1.5-flash"  # Balance
    else:
        return "gemini-1.5-flash"  # Budget mode
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `per_invoice_target` | $0.003 | Project requirement |
| `per_invoice_warning` | $0.005 | Warning threshold |
| `per_invoice_critical` | $0.010 | Critical threshold |
| `daily_budget` | $100 | Daily spending cap |

## Example Usage

```python
# Process with cost monitoring
result = process_with_cost_monitoring(image_bytes)
print(f"Cost: ${result['cost']:.4f}")

# Check if within budget
if result['cost'] <= THRESHOLDS.per_invoice_target:
    print("Within budget")
```

## See Also

- [Cost Tracking](../concepts/cost-tracking.md)
- [Dashboard Metrics](../patterns/dashboard-metrics.md)
- [Model Comparison](../concepts/model-comparison.md)
