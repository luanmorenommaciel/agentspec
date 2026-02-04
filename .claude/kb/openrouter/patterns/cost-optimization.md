# Cost Optimization

> **Purpose**: Price-based routing, :floor variant, budget controls, and cost reduction strategies
> **MCP Validated**: 2026-01-28

## When to Use

- Batch processing where latency is less critical than cost
- Development/testing environments with budget constraints
- High-volume applications needing cost visibility
- Multi-tier pricing strategies (cheap for simple, premium for complex)

## Implementation

```python
import os
from openai import OpenAI
from typing import Optional

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# =============================================================================
# Strategy 1: Use :floor Variant for Cheapest Provider
# =============================================================================

def cheap_completion(messages: list, model: str = "openai/gpt-4o") -> str:
    """Route to cheapest provider using :floor variant."""
    response = client.chat.completions.create(
        model=f"{model}:floor",  # Append :floor for cost optimization
        messages=messages
    )
    return response.choices[0].message.content


# =============================================================================
# Strategy 2: Max Price Filtering
# =============================================================================

def budget_completion(
    messages: list,
    model: str = "openai/gpt-4o",
    max_prompt_price: float = 1.0,   # $/million tokens
    max_completion_price: float = 2.0
) -> str:
    """Only use providers under specified price thresholds."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        extra_body={
            "provider": {
                "sort": "price",
                "max_price": {
                    "prompt": max_prompt_price,
                    "completion": max_completion_price
                }
            }
        }
    )
    return response.choices[0].message.content


# =============================================================================
# Strategy 3: Tiered Model Selection
# =============================================================================

def tiered_completion(
    messages: list,
    complexity: str = "simple"  # "simple", "medium", "complex"
) -> str:
    """Route to different models based on task complexity."""
    model_tiers = {
        "simple": "google/gemma-3-12b:free",      # Free tier
        "medium": "openai/gpt-4o-mini:floor",     # Budget tier
        "complex": "anthropic/claude-4-sonnet"    # Premium tier
    }

    model = model_tiers.get(complexity, model_tiers["medium"])

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content


# =============================================================================
# Strategy 4: Token Counting for Pre-Request Cost Estimation
# =============================================================================

def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    prompt_price: float,     # per million tokens
    completion_price: float  # per million tokens
) -> float:
    """Estimate cost before making request."""
    prompt_cost = (prompt_tokens / 1_000_000) * prompt_price
    completion_cost = (completion_tokens / 1_000_000) * completion_price
    return prompt_cost + completion_cost
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_price.prompt` | None | Max $/M for input tokens |
| `max_price.completion` | None | Max $/M for output tokens |
| `sort` | Default | `"price"` for cheapest first |
| `:floor` variant | N/A | Append to model name |

## Example Usage

```python
# Simple cost optimization with :floor
response = cheap_completion(
    [{"role": "user", "content": "Summarize this text..."}]
)

# Strict budget control
response = budget_completion(
    [{"role": "user", "content": "Analyze data..."}],
    max_prompt_price=0.5,
    max_completion_price=1.5
)

# Tiered routing based on task
simple_response = tiered_completion(
    [{"role": "user", "content": "What is 2+2?"}],
    complexity="simple"  # Uses free model
)

complex_response = tiered_completion(
    [{"role": "user", "content": "Write a research paper..."}],
    complexity="complex"  # Uses premium model
)

# Pre-request cost estimation
estimated = estimate_cost(
    prompt_tokens=1000,
    completion_tokens=500,
    prompt_price=3.0,
    completion_price=15.0
)
print(f"Estimated cost: ${estimated:.6f}")
```

## See Also

- [model-selection.md](../concepts/model-selection.md)
- [provider-routing.md](../patterns/provider-routing.md)
- [rate-limits.md](../concepts/rate-limits.md)
