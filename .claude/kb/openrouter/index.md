# OpenRouter Knowledge Base

> **Purpose**: Unified LLM API gateway providing access to 400+ AI models through a single endpoint with automatic fallback, load balancing, and cost optimization
> **MCP Validated**: 2026-01-28

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/api-basics.md](concepts/api-basics.md) | Core API structure, endpoints, and request/response format |
| [concepts/authentication.md](concepts/authentication.md) | API keys, Bearer tokens, OAuth PKCE, and BYOK setup |
| [concepts/model-selection.md](concepts/model-selection.md) | Choosing models, routing variants, and auto-routing |
| [concepts/streaming.md](concepts/streaming.md) | SSE streaming, chunk handling, and stream methods |
| [concepts/rate-limits.md](concepts/rate-limits.md) | Rate limiting tiers, quotas, and credit-based limits |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/python-sdk-integration.md](patterns/python-sdk-integration.md) | Official SDK and OpenAI SDK integration patterns |
| [patterns/cost-optimization.md](patterns/cost-optimization.md) | Price-based routing, :floor variant, and budget controls |
| [patterns/error-handling.md](patterns/error-handling.md) | Fallback chains, retry strategies, and debug mode |
| [patterns/provider-routing.md](patterns/provider-routing.md) | Provider selection, :nitro variant, and max_price filtering |
| [patterns/langchain-integration.md](patterns/langchain-integration.md) | ChatOpenRouter class and LCEL streaming |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables for models, pricing, and routing

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Unified API** | Single endpoint (https://openrouter.ai/api/v1) for 400+ models from OpenAI, Anthropic, Google, Meta, Mistral |
| **OpenAI Compatibility** | Drop-in replacement using OpenAI SDK with base_url override |
| **Dynamic Routing** | :nitro (throughput), :floor (cost), and auto model selection |
| **Provider Fallback** | Automatic failover when primary provider returns errors |
| **Credit System** | Prepaid credits deducted per request based on token usage |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/api-basics.md, concepts/authentication.md |
| **Intermediate** | concepts/model-selection.md, patterns/python-sdk-integration.md |
| **Advanced** | patterns/cost-optimization.md, patterns/provider-routing.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| LLMOps Agent | patterns/cost-optimization.md, concepts/rate-limits.md | Monitor and optimize LLM costs |
| Integration Agent | patterns/python-sdk-integration.md, patterns/langchain-integration.md | Connect applications to OpenRouter |
| Reliability Agent | patterns/error-handling.md, patterns/provider-routing.md | Build resilient LLM pipelines |
