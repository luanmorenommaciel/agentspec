# Streaming

> **Purpose**: SSE streaming, chunk handling, and stream methods in OpenRouter
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-28

## Overview

OpenRouter supports Server-Sent Events (SSE) streaming for real-time token delivery. Enable streaming by setting `stream: true` in your request. The SDK provides multiple streaming patterns: text streaming, reasoning streaming, items streaming, and tool call streaming. Errors during streaming are delivered as SSE events.

## The Pattern

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Basic streaming with OpenAI SDK
def stream_response(messages: list, model: str = "anthropic/claude-4-sonnet"):
    """Stream response chunks as they arrive."""
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
    )

    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content

    print()  # Newline after streaming
    return full_response

# Usage
response = stream_response([
    {"role": "user", "content": "Explain quantum computing."}
])
```

## Quick Reference

| Stream Type | Method | Use Case |
|-------------|--------|----------|
| Text | `stream=True` | Token-by-token output |
| Reasoning | `getReasoningStream()` | Chain-of-thought |
| Items | `getItemsStream()` | Structured outputs |
| Tool calls | `getToolCallsStream()` | Function calling |

## Common Mistakes

### Wrong

```python
# Not handling streaming errors properly
for chunk in stream:
    # Wrong: ignoring potential error events
    print(chunk.choices[0].delta.content)
```

### Correct

```python
# Proper streaming with error handling
for chunk in stream:
    # Check for error in chunk (SSE error event)
    if hasattr(chunk, 'error'):
        raise Exception(f"Stream error: {chunk.error}")

    # Check if content exists before accessing
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## Async Streaming

```python
import asyncio
from openai import AsyncOpenAI

async def async_stream(messages: list):
    client = AsyncOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    stream = await client.chat.completions.create(
        model="anthropic/claude-4-sonnet",
        messages=messages,
        stream=True
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
```

## Related

- [api-basics.md](../concepts/api-basics.md)
- [error-handling.md](../patterns/error-handling.md)
- [python-sdk-integration.md](../patterns/python-sdk-integration.md)
