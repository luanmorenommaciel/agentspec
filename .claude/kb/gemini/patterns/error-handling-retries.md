# Error Handling and Retries Pattern

> **Purpose**: Build robust API interactions with proper error handling
> **MCP Validated**: 2026-01-25

## When to Use

- Production deployments requiring reliability
- Handling transient API failures
- Managing rate limits (429 errors)
- Graceful degradation strategies

## Implementation

```python
from google import genai
from google.genai import types
import time
import json
from typing import Optional, Callable, TypeVar
from functools import wraps
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retryable_codes: tuple = (429, 500, 502, 503, 504)


class GeminiError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(GeminiError):
    pass


class SafetyBlockError(GeminiError):
    def __init__(self, message: str, blocked_categories: list):
        super().__init__(message)
        self.blocked_categories = blocked_categories


def with_retry(config: RetryConfig = None):
    """Decorator for automatic retry with exponential backoff."""
    config = config or RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    code = getattr(e, 'status_code', None)
                    if code not in config.retryable_codes:
                        raise
                    delay = min(config.base_delay * (config.exponential_base ** attempt),
                               config.max_delay)
                    time.sleep(delay)
            raise last_error
        return wrapper
    return decorator


class RobustGeminiClient:
    """Gemini client with built-in error handling and retries."""

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.client = genai.Client(vertexai=True, project=project_id, location=location)

    @with_retry()
    def generate(self, model: str, contents: list, config: types.GenerateContentConfig) -> str:
        response = self.client.models.generate_content(model=model, contents=contents, config=config)
        if hasattr(response, 'candidates') and response.candidates:
            if response.candidates[0].finish_reason == "SAFETY":
                blocked = [r.category for r in response.candidates[0].safety_ratings
                          if getattr(r, 'blocked', False)]
                raise SafetyBlockError("Blocked", blocked)
        return response.text

    def extract_with_fallback(self, prompt: str, content: types.Content, schema: dict,
                               models: list = None) -> dict:
        models = models or ["gemini-2.5-flash", "gemini-2.5-pro"]
        for model in models:
            try:
                result = self.generate(model=model,
                    contents=[types.Content(parts=[types.Part(text=prompt)]), content],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json", response_schema=schema))
                return json.loads(result)
            except SafetyBlockError:
                raise
            except Exception:
                continue
        raise GeminiError("All models failed")
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_retries` | 3 | Maximum retry attempts |
| `base_delay` | 1.0s | Initial backoff delay |
| `max_delay` | 60.0s | Maximum backoff delay |
| `exponential_base` | 2.0 | Backoff multiplier |

## Example Usage

```python
client = RobustGeminiClient(project_id="my-project")

try:
    result = client.extract_with_fallback(
        prompt="Extract invoice data.",
        content=image_content,
        schema=invoice_schema
    )
except SafetyBlockError as e:
    print(f"Safety block: {e.blocked_categories}")
except RateLimitError:
    print("Rate limited - try again later")
except GeminiError as e:
    print(f"API error: {e}")
```

## See Also

- [openrouter-fallback.md](openrouter-fallback.md)
- [batch-processing.md](batch-processing.md)
- [../concepts/safety-settings.md](../concepts/safety-settings.md)
