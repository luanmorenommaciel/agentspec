# Gemini Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-01-25

## Model Comparison (January 2026)

| Model | Input/1M | Output/1M | Context | Best For |
|-------|----------|-----------|---------|----------|
| gemini-2.5-flash-lite | $0.10 | $0.40 | 1M | High-volume, low-cost |
| gemini-2.5-flash | $0.15 | $0.60 | 1M | Balanced speed/quality |
| gemini-2.5-pro | $1.25 | $5.00 | 1M | Complex reasoning |
| gemini-3-pro-preview | $2.00 | $12.00 | 1M | Cutting-edge tasks |

## Token Costs by Media Type

| Input Type | Tokens | Approx Cost |
|------------|--------|-------------|
| 1 image (any size) | ~258-1290 | $0.0001-0.0013 |
| 1 second video | 258 | $0.00003 |
| 1K text chars | ~250 | $0.000025 |

## SDK Quick Setup

| Step | Code |
|------|------|
| Install | `pip install google-genai` |
| Init Vertex | `client = genai.Client(vertexai=True, project="ID", location="us-central1")` |
| Init API Key | `client = genai.Client(api_key="KEY")` |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Invoice extraction | gemini-2.5-flash + vision |
| Batch processing (1000+ docs) | gemini-2.5-flash-lite |
| Complex multi-step reasoning | gemini-2.5-pro |
| Cost-sensitive production | OpenRouter fallback chain |

## Safety Thresholds

| Setting | Behavior |
|---------|----------|
| BLOCK_NONE | No blocking (careful!) |
| BLOCK_LOW_AND_ABOVE | Block low+ probability |
| BLOCK_MEDIUM_AND_ABOVE | Block medium+ probability |
| BLOCK_ONLY_HIGH | Block high probability only |

## Common Pitfalls

| Mistake | Fix |
|---------|-----|
| Using deprecated vertexai.generative_models | Use google-genai SDK |
| Ignoring responseSchema ordering | Match schema order in prompts |
| Not handling 429 rate limits | Implement exponential backoff |
| Skipping safety settings | Configure for document tasks |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GOOGLE_GENAI_USE_VERTEXAI` | Enable Vertex AI mode |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | Region (us-central1) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account JSON path |

## Related Documentation

| Topic | Path |
|-------|------|
| Model Capabilities | `concepts/model-capabilities.md` |
| Full Index | `index.md` |
