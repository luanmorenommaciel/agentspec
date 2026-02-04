# Provider Routing

> **Purpose**: Provider selection, :nitro variant, max_price filtering, and intelligent routing strategies
> **MCP Validated**: 2026-01-28

## When to Use

- Need specific provider characteristics (latency, compliance, location)
- Optimizing for throughput in real-time applications
- Excluding certain providers for compliance reasons
- Building multi-provider load balancing strategies

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
# Strategy 1: Throughput Optimization with :nitro
# =============================================================================

def fast_completion(messages: list, model: str = "openai/gpt-4o") -> str:
    """Route to fastest provider using :nitro variant."""
    response = client.chat.completions.create(
        model=f"{model}:nitro",  # Append :nitro for speed
        messages=messages
    )
    return response.choices[0].message.content


# =============================================================================
# Strategy 2: Provider Ordering
# =============================================================================

def completion_with_provider_order(
    messages: list,
    model: str = "openai/gpt-4o",
    provider_order: list = None
) -> str:
    """Specify preferred provider order."""
    if provider_order is None:
        provider_order = ["Anthropic", "OpenAI", "Google"]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        extra_body={
            "provider": {
                "order": provider_order
            }
        }
    )
    return response.choices[0].message.content


# =============================================================================
# Strategy 3: Combined Routing (Speed + Budget)
# =============================================================================

def optimized_completion(
    messages: list,
    model: str = "openai/gpt-4o",
    sort_by: str = "throughput",  # "throughput" or "price"
    max_prompt_price: float = None,
    max_completion_price: float = None
) -> str:
    """Optimize for throughput while respecting budget."""
    provider_config = {"sort": sort_by}

    if max_prompt_price and max_completion_price:
        provider_config["max_price"] = {
            "prompt": max_prompt_price,
            "completion": max_completion_price
        }

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        extra_body={"provider": provider_config}
    )
    return response.choices[0].message.content


# =============================================================================
# Strategy 4: Provider Exclusion
# =============================================================================

def completion_exclude_providers(
    messages: list,
    model: str = "openai/gpt-4o",
    exclude: list = None
) -> str:
    """Exclude specific providers (e.g., for compliance)."""
    if exclude is None:
        exclude = []

    # Use order to implicitly exclude by only listing allowed providers
    all_providers = ["OpenAI", "Anthropic", "Google", "Together", "Fireworks"]
    allowed = [p for p in all_providers if p not in exclude]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        extra_body={
            "provider": {
                "order": allowed,
                "allow_fallbacks": False  # Strict: only use listed providers
            }
        }
    )
    return response.choices[0].message.content


# =============================================================================
# Strategy 5: Quantized Models for Cost/Speed
# =============================================================================

def quantized_completion(messages: list) -> str:
    """Use quantized model variants for reduced cost."""
    # Quantized models (FP8, INT8) offer lower cost with slight quality tradeoff
    response = client.chat.completions.create(
        model="meta-llama/llama-3-70b-instruct:nitro",  # Often quantized
        messages=messages,
        extra_body={
            "provider": {
                "sort": "throughput",
                "quantizations": ["fp8", "int8"]  # Prefer quantized
            }
        }
    )
    return response.choices[0].message.content
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `sort` | Default | `"throughput"` or `"price"` |
| `order` | None | Provider preference array |
| `allow_fallbacks` | true | Fall back to other providers |
| `quantizations` | None | Preferred quantization types |
| `:nitro` | N/A | Append to model for speed |

## Example Usage

```python
# Fastest response
fast_response = fast_completion(
    [{"role": "user", "content": "Quick answer needed!"}]
)

# Prefer specific providers
response = completion_with_provider_order(
    [{"role": "user", "content": "Analyze..."}],
    provider_order=["Anthropic", "OpenAI"]
)

# Fast but budget-conscious
response = optimized_completion(
    [{"role": "user", "content": "Process this..."}],
    sort_by="throughput",
    max_prompt_price=1.0,
    max_completion_price=3.0
)

# Compliance: exclude certain providers
response = completion_exclude_providers(
    [{"role": "user", "content": "Sensitive data..."}],
    exclude=["Together", "Fireworks"]
)
```

## See Also

- [model-selection.md](../concepts/model-selection.md)
- [cost-optimization.md](../patterns/cost-optimization.md)
- [error-handling.md](../patterns/error-handling.md)
