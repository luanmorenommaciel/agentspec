# API Basics

> **Purpose**: Core API structure, endpoints, and request/response format for OpenRouter
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-28

## Overview

OpenRouter provides a unified API gateway to 400+ LLM models through a single OpenAI-compatible endpoint. The API normalizes request/response schemas across all providers (OpenAI, Anthropic, Google, Meta, Mistral) so you only need to learn one interface. The base URL is `https://openrouter.ai/api/v1`.

## The Pattern

```python
import requests
import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

def chat_completion(messages: list, model: str = "openai/gpt-4o") -> dict:
    """Basic chat completion using OpenRouter API."""
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-app.com",  # Optional
            "X-Title": "Your App Name"               # Optional
        },
        json={
            "model": model,
            "messages": messages
        }
    )
    return response.json()

# Usage
result = chat_completion([
    {"role": "user", "content": "Hello, how are you?"}
])
print(result["choices"][0]["message"]["content"])
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `model: "anthropic/claude-4-sonnet"` | Routes to Anthropic | Provider prefix required |
| `model: "openai/gpt-4o"` | Routes to OpenAI | Default load balancing |
| `model: "auto"` | Auto-selects best model | Based on prompt analysis |

## Common Mistakes

### Wrong

```python
# Missing provider prefix - will fail
response = requests.post(url, json={
    "model": "gpt-4o",  # Wrong: no provider prefix
    "messages": messages
})
```

### Correct

```python
# Include provider prefix in model name
response = requests.post(url, json={
    "model": "openai/gpt-4o",  # Correct: provider/model format
    "messages": messages
})
```

## Related

- [authentication.md](../concepts/authentication.md)
- [model-selection.md](../concepts/model-selection.md)
- [python-sdk-integration.md](../patterns/python-sdk-integration.md)
