# Rate Limits

> **Purpose**: Rate limiting tiers, quotas, and credit-based limits in OpenRouter
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-28

## Overview

OpenRouter uses a credit-based system where rate limits for free models depend on your credit balance. Paid models have per-provider limits that vary by model and provider. Rate limits are applied per API key and reset daily for free models. The platform handles provider-specific rate limiting and can automatically failover when limits are reached.

## The Pattern

```python
import os
import time
from openai import OpenAI, RateLimitError

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def make_request_with_retry(messages: list, max_retries: int = 3):
    """Make request with exponential backoff on rate limits."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-4o",
                messages=messages
            )
            return response
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)

    return None

# Usage
response = make_request_with_retry([
    {"role": "user", "content": "Hello!"}
])
```

## Quick Reference

| Credit Balance | Free Model Limit | Reset |
|----------------|------------------|-------|
| >= $10 | 1000 requests/day | Daily |
| < $10 | 50 requests/day | Daily |
| $0 | Varies by model | Daily |

## Common Mistakes

### Wrong

```python
# Not handling rate limits at all
def make_request(messages):
    # Will crash on rate limit
    return client.chat.completions.create(
        model="google/gemma-3-12b:free",
        messages=messages
    )

# Tight loop without delay
for i in range(1000):
    make_request(messages)  # Will hit rate limit
```

### Correct

```python
import random

def make_request_with_backoff(messages, max_retries=5):
    """Exponential backoff with jitter."""
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model="google/gemma-3-12b:free",
                messages=messages
            )
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            # Exponential backoff with jitter
            base_wait = 2 ** attempt
            jitter = random.uniform(0, 1)
            time.sleep(base_wait + jitter)
```

## Check Rate Limit Status

```python
import requests

def check_api_key_info():
    """Check current API key rate limit status."""
    response = requests.get(
        "https://openrouter.ai/api/v1/auth/key",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
        }
    )
    return response.json()

# Returns: {"data": {"label": "key-name", "limit": 1000, "usage": 42, ...}}
```

## Related

- [authentication.md](../concepts/authentication.md)
- [error-handling.md](../patterns/error-handling.md)
- [cost-optimization.md](../patterns/cost-optimization.md)
