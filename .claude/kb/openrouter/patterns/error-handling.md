# Error Handling

> **Purpose**: Fallback chains, retry strategies, and debug mode for resilient OpenRouter applications
> **MCP Validated**: 2026-01-28

## When to Use

- Production applications requiring high availability
- Multi-model workflows with graceful degradation
- Development environments needing detailed error diagnostics
- High-volume systems with automatic recovery

## Implementation

```python
import os
import time
import random
from typing import Optional
from openai import OpenAI, APIError, RateLimitError, APIConnectionError

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# =============================================================================
# Strategy 1: Model Fallback Chain
# =============================================================================

def completion_with_fallbacks(
    messages: list,
    models: list = None
) -> tuple[str, str]:
    """Try multiple models in sequence until one succeeds."""
    if models is None:
        models = [
            "anthropic/claude-4-sonnet",
            "openai/gpt-4o",
            "google/gemini-2.0-flash"
        ]

    last_error = None

    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            return response.choices[0].message.content, model
        except APIError as e:
            last_error = e
            print(f"Model {model} failed: {e}")
            continue

    raise last_error or Exception("All models failed")


# =============================================================================
# Strategy 2: Exponential Backoff with Jitter
# =============================================================================

def completion_with_retry(
    messages: list,
    model: str = "openai/gpt-4o",
    max_retries: int = 5,
    base_delay: float = 1.0
) -> str:
    """Retry with exponential backoff and jitter."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            return response.choices[0].message.content

        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"Rate limited. Retrying in {delay:.2f}s...")
            time.sleep(delay)

        except APIConnectionError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"Connection error. Retrying in {delay:.2f}s...")
            time.sleep(delay)

    return None


# =============================================================================
# Strategy 3: OpenRouter Built-in Fallbacks
# =============================================================================

def completion_with_openrouter_fallbacks(messages: list) -> str:
    """Use OpenRouter's built-in model fallback feature."""
    response = client.chat.completions.create(
        model="anthropic/claude-4-sonnet",  # Primary
        messages=messages,
        extra_body={
            "models": [
                "anthropic/claude-4-sonnet",
                "openai/gpt-4o",
                "google/gemini-2.0-flash"
            ]
        }
    )
    return response.choices[0].message.content


# =============================================================================
# Strategy 4: Debug Mode (Development Only)
# =============================================================================

def completion_with_debug(messages: list) -> dict:
    """Enable debug mode to see provider selection details.

    WARNING: Do not use in production - may expose sensitive info.
    """
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=messages,
        extra_body={"debug": True}
    )

    # Debug info available in response headers/metadata
    return {
        "content": response.choices[0].message.content,
        "model": response.model,
        "usage": response.usage
    }
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `models` (array) | None | Fallback model chain |
| `debug` | false | Enable debug mode (dev only) |
| `allow_fallbacks` | true | Allow provider fallbacks |
| `max_retries` | 5 | Application retry attempts |

## Example Usage

```python
# Model fallback chain
content, used_model = completion_with_fallbacks(
    [{"role": "user", "content": "Hello!"}]
)
print(f"Used model: {used_model}")

# Retry with backoff
response = completion_with_retry(
    [{"role": "user", "content": "Analyze this..."}],
    max_retries=3
)

# OpenRouter native fallbacks
response = completion_with_openrouter_fallbacks(
    [{"role": "user", "content": "Complex query..."}]
)

# Debug mode for development
if os.getenv("ENV") == "development":
    debug_info = completion_with_debug(
        [{"role": "user", "content": "Test"}]
    )
    print(f"Debug: {debug_info}")
```

## See Also

- [rate-limits.md](../concepts/rate-limits.md)
- [streaming.md](../concepts/streaming.md)
- [provider-routing.md](../patterns/provider-routing.md)
