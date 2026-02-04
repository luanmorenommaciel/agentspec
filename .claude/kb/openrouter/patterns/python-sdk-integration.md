# Python SDK Integration

> **Purpose**: Official OpenRouter SDK and OpenAI SDK integration patterns for Python applications
> **MCP Validated**: 2026-01-28

## When to Use

- Building Python applications that need access to multiple LLM providers
- Migrating from OpenAI SDK to use additional models
- Creating production services that require provider fallbacks
- Developing with type-safe SDK features and async support

## Implementation

```python
import os
from openai import OpenAI, AsyncOpenAI

# =============================================================================
# Method 1: OpenAI SDK (Recommended for most use cases)
# =============================================================================

def create_openrouter_client() -> OpenAI:
    """Create OpenRouter client using OpenAI SDK."""
    return OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": os.getenv("APP_URL", "https://localhost"),
            "X-Title": os.getenv("APP_NAME", "My App")
        }
    )


def chat_completion(
    client: OpenAI,
    messages: list,
    model: str = "anthropic/claude-4-sonnet",
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> str:
    """Basic chat completion with OpenRouter."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


# =============================================================================
# Method 2: Async Client for High-Throughput Applications
# =============================================================================

async def async_chat_completion(
    messages: list,
    model: str = "anthropic/claude-4-sonnet"
) -> str:
    """Async chat completion for concurrent requests."""
    client = AsyncOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    response = await client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content


# =============================================================================
# Method 3: With Provider Routing Options
# =============================================================================

def chat_with_routing(
    client: OpenAI,
    messages: list,
    model: str = "openai/gpt-4o",
    sort_by: str = "price",  # "price" or "throughput"
    max_price_prompt: float = None,
    max_price_completion: float = None
) -> str:
    """Chat completion with provider routing options."""
    extra_body = {"provider": {"sort": sort_by}}

    if max_price_prompt and max_price_completion:
        extra_body["provider"]["max_price"] = {
            "prompt": max_price_prompt,
            "completion": max_price_completion
        }

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        extra_body=extra_body
    )
    return response.choices[0].message.content
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `OPENROUTER_API_KEY` | Required | Your OpenRouter API key |
| `APP_URL` | localhost | Your app URL for HTTP-Referer header |
| `APP_NAME` | My App | Your app name for X-Title header |
| `base_url` | Required | `https://openrouter.ai/api/v1` |

## Example Usage

```python
# Basic usage
client = create_openrouter_client()

response = chat_completion(
    client,
    messages=[{"role": "user", "content": "Explain REST APIs"}],
    model="anthropic/claude-4-sonnet"
)
print(response)

# With cost optimization
cheap_response = chat_with_routing(
    client,
    messages=[{"role": "user", "content": "Quick question"}],
    model="openai/gpt-4o:floor",
    sort_by="price"
)

# Async batch processing
import asyncio

async def process_batch(prompts: list):
    tasks = [
        async_chat_completion([{"role": "user", "content": p}])
        for p in prompts
    ]
    return await asyncio.gather(*tasks)

results = asyncio.run(process_batch(["Q1", "Q2", "Q3"]))
```

## See Also

- [api-basics.md](../concepts/api-basics.md)
- [streaming.md](../concepts/streaming.md)
- [langchain-integration.md](../patterns/langchain-integration.md)
