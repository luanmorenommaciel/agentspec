# OpenRouter Fallback Pattern

> **Purpose**: Implement multi-provider resilience with automatic failover
> **MCP Validated**: 2026-01-25

## When to Use

- Production systems requiring high availability
- Cost optimization across providers
- Handling Vertex AI rate limits or outages
- A/B testing different model providers

## Implementation

```python
from google import genai
from google.genai import types
from openai import OpenAI
import json
import time
from dataclasses import dataclass
from enum import Enum


class Provider(Enum):
    VERTEX_AI = "vertex_ai"
    OPENROUTER = "openrouter"


@dataclass
class ExtractionResult:
    data: dict
    provider: Provider
    model: str
    latency_ms: float


class MultiProviderExtractor:
    """Extract data with automatic fallback across providers."""

    def __init__(self, gcp_project: str, openrouter_api_key: str, gcp_location: str = "us-central1"):
        self.vertex_client = genai.Client(vertexai=True, project=gcp_project, location=gcp_location)
        self.openrouter_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_api_key)
        self.vertex_model = "gemini-2.5-flash"
        self.openrouter_models = ["google/gemini-2.5-flash", "google/gemini-2.5-pro", "anthropic/claude-3.5-sonnet"]

    def extract(self, prompt: str, image_data: str, mime_type: str, schema: dict) -> ExtractionResult:
        # Try Vertex AI first
        try:
            start = time.time()
            result = self._extract_vertex(prompt, image_data, mime_type, schema)
            return ExtractionResult(data=result, provider=Provider.VERTEX_AI,
                                   model=self.vertex_model, latency_ms=(time.time() - start) * 1000)
        except Exception as e:
            print(f"Vertex AI failed: {e}")

        # Fallback to OpenRouter
        start = time.time()
        result, model = self._extract_openrouter(prompt, image_data, schema)
        return ExtractionResult(data=result, provider=Provider.OPENROUTER,
                               model=model, latency_ms=(time.time() - start) * 1000)

    def _extract_vertex(self, prompt: str, image_data: str, mime_type: str, schema: dict) -> dict:
        content = types.Content(parts=[
            types.Part(text=prompt),
            types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_data))
        ])
        response = self.vertex_client.models.generate_content(
            model=self.vertex_model, contents=[content],
            config=types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=schema, temperature=0.3))
        return json.loads(response.text)

    def _extract_openrouter(self, prompt: str, image_data: str, schema: dict) -> tuple[dict, str]:
        for model in self.openrouter_models:
            try:
                response = self.openrouter_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                    ]}],
                    response_format={"type": "json_object"}, temperature=0.3)
                return json.loads(response.choices[0].message.content), model
            except Exception as e:
                print(f"OpenRouter {model} failed: {e}")
        raise RuntimeError("All providers failed")
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| Primary provider | Vertex AI | Lower cost, better integration |
| Fallback provider | OpenRouter | Multi-model access |
| Timeout | 30s per provider | Prevent hanging |

## Example Usage

```python
import os
import base64

extractor = MultiProviderExtractor(
    gcp_project="my-project",
    openrouter_api_key=os.environ["OPENROUTER_API_KEY"]
)

with open("invoice.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

result = extractor.extract(
    prompt="Extract invoice data.",
    image_data=image_data,
    mime_type="image/png",
    schema={"type": "object", "properties": {"total": {"type": "number"}}}
)

print(f"Provider: {result.provider.value}, Model: {result.model}")
```

## See Also

- [error-handling-retries.md](error-handling-retries.md)
- [../concepts/vertex-ai-integration.md](../concepts/vertex-ai-integration.md)
