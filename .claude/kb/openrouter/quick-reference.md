# OpenRouter Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-01-28

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/chat/completions` | POST | Chat completions (OpenAI-compatible) |
| `/api/v1/models` | GET | List available models |
| `/api/v1/auth/keys` | POST | Exchange OAuth code for API key |
| `/api/v1/generation` | GET | Get generation stats by ID |

## Routing Variants

| Variant | Behavior | Use Case |
|---------|----------|----------|
| `model-name` | Default load balancing | Standard usage |
| `model-name:nitro` | Sort by throughput | Low latency required |
| `model-name:floor` | Sort by price | Cost optimization |

## Common Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization: Bearer <key>` | Yes | API authentication |
| `HTTP-Referer` | No | Your app URL (for rankings) |
| `X-Title` | No | Your app name (for rankings) |
| `Content-Type: application/json` | Yes | Request format |

## Provider Parameters

| Parameter | Type | Example |
|-----------|------|---------|
| `sort` | string | `"price"`, `"throughput"` |
| `max_price` | object | `{"prompt": 1, "completion": 2}` |
| `order` | array | `["Anthropic", "OpenAI"]` |
| `allow_fallbacks` | boolean | `true` (default) |

## Rate Limits (Free Models)

| Credit Balance | Daily Limit |
|----------------|-------------|
| >= $10 credits | 1000 requests/day |
| < $10 credits | 50 requests/day |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Fastest response | `:nitro` variant |
| Lowest cost | `:floor` variant |
| Specific provider | `provider.order` parameter |
| Budget cap | `provider.max_price` parameter |
| High reliability | `models` array with fallbacks |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Use debug in production | Use debug only in development |
| Ignore streaming errors | Handle SSE error events |
| Skip token counting | Count tokens before large requests |
| Hardcode single model | Use fallback model chains |

## Related Documentation

| Topic | Path |
|-------|------|
| Getting Started | `concepts/api-basics.md` |
| Authentication | `concepts/authentication.md` |
| Full Index | `index.md` |
