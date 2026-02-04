# Authentication

> **Purpose**: API keys, Bearer tokens, OAuth PKCE, and BYOK setup for OpenRouter
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-28

## Overview

OpenRouter authenticates requests using Bearer tokens in the Authorization header. API keys are created in your OpenRouter dashboard and are more powerful than direct provider keys since they provide access to all models. For user-facing apps, OAuth PKCE flow allows users to authenticate with their own OpenRouter accounts.

## The Pattern

```python
import os
from openai import OpenAI

# Method 1: Direct API Key (most common)
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Method 2: With optional headers for app attribution
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://your-app.com",
        "X-Title": "Your App Name"
    }
)

# Make authenticated request
response = client.chat.completions.create(
    model="anthropic/claude-4-sonnet",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Quick Reference

| Auth Method | Use Case | Setup |
|-------------|----------|-------|
| `Bearer <api_key>` | Server-side apps | Create key in dashboard |
| OAuth PKCE | User-facing apps | Redirect to `/auth` endpoint |
| BYOK | Use own provider keys | Configure in dashboard |

## Common Mistakes

### Wrong

```python
# API key in query params - insecure and won't work
response = requests.get(
    f"{BASE_URL}/models?api_key={api_key}"  # Wrong!
)

# Missing Bearer prefix
headers = {"Authorization": api_key}  # Wrong!
```

### Correct

```python
# API key in Authorization header with Bearer prefix
headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
}

response = requests.get(f"{BASE_URL}/models", headers=headers)
```

## OAuth PKCE Flow

```python
# Step 1: Redirect user to OpenRouter auth
auth_url = "https://openrouter.ai/auth"
callback_url = "https://your-app.com/callback"
redirect_url = f"{auth_url}?callback_url={callback_url}"

# Step 2: Exchange code for API key (in callback handler)
def exchange_code(code: str) -> str:
    response = requests.post(
        "https://openrouter.ai/api/v1/auth/keys",
        json={"code": code}
    )
    return response.json()["key"]
```

## Related

- [api-basics.md](../concepts/api-basics.md)
- [rate-limits.md](../concepts/rate-limits.md)
- [python-sdk-integration.md](../patterns/python-sdk-integration.md)
