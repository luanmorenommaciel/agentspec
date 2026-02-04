# Model Selection

> **Purpose**: Choosing models, routing variants, and auto-routing in OpenRouter
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-28

## Overview

OpenRouter provides access to 400+ models from multiple providers. Models are identified by `provider/model-name` format. Dynamic routing variants (`:nitro`, `:floor`) modify provider selection behavior. Auto model selection eliminates branching logic and provides intelligent routing based on your requirements.

## The Pattern

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Explicit model selection
response = client.chat.completions.create(
    model="anthropic/claude-4-sonnet",
    messages=[{"role": "user", "content": "Analyze this data..."}]
)

# Routing variants for optimization
# :nitro - prioritize throughput (fastest response)
response = client.chat.completions.create(
    model="openai/gpt-4o:nitro",
    messages=[{"role": "user", "content": "Quick question..."}]
)

# :floor - prioritize cost (cheapest provider)
response = client.chat.completions.create(
    model="openai/gpt-4o:floor",
    messages=[{"role": "user", "content": "Batch processing..."}]
)
```

## Quick Reference

| Model Format | Behavior | Example |
|--------------|----------|---------|
| `provider/model` | Default routing | `anthropic/claude-4-sonnet` |
| `model:nitro` | Fastest provider | `openai/gpt-4o:nitro` |
| `model:floor` | Cheapest provider | `openai/gpt-4o:floor` |
| `auto` | Intelligent selection | Based on prompt |

## Common Mistakes

### Wrong

```python
# Using model name without provider prefix
response = client.chat.completions.create(
    model="claude-4-sonnet",  # Wrong: missing provider
    messages=messages
)

# Mixing routing variants incorrectly
response = client.chat.completions.create(
    model="openai/gpt-4o:nitro:floor",  # Wrong: can't combine
    messages=messages
)
```

### Correct

```python
# Always include provider prefix
response = client.chat.completions.create(
    model="anthropic/claude-4-sonnet",  # Correct
    messages=messages
)

# Use one routing variant at a time
response = client.chat.completions.create(
    model="openai/gpt-4o:floor",  # Correct: single variant
    messages=messages
)
```

## Model Fallback Chain

```python
# Define fallback models for reliability
response = client.chat.completions.create(
    model="anthropic/claude-4-sonnet",
    messages=messages,
    extra_body={
        "models": [
            "anthropic/claude-4-sonnet",
            "openai/gpt-4o",
            "google/gemini-2.0-flash"
        ]
    }
)
```

## Related

- [api-basics.md](../concepts/api-basics.md)
- [provider-routing.md](../patterns/provider-routing.md)
- [cost-optimization.md](../patterns/cost-optimization.md)
