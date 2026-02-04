# Langfuse Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-01-25

## SDK Installation

| Action | Command |
|--------|---------|
| Install | `pip install langfuse` |
| Initialize | `from langfuse import get_client; langfuse = get_client()` |
| Verify | `langfuse.auth_check()` |
| Flush | `langfuse.flush()` |

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LANGFUSE_SECRET_KEY` | API secret key | `sk-lf-...` |
| `LANGFUSE_PUBLIC_KEY` | API public key | `pk-lf-...` |
| `LANGFUSE_BASE_URL` | Server endpoint | `https://cloud.langfuse.com` |

## Observation Types

| Type | Use Case | Tracks |
|------|----------|--------|
| `span` | Generic operations | Duration, I/O |
| `generation` | LLM calls | Model, tokens, cost |
| `event` | Discrete points | Timestamp only |
| `tool` | Tool invocations | Function calls |
| `retriever` | RAG retrieval | Document fetch |

## Score Data Types

| Type | Values | Example |
|------|--------|---------|
| `NUMERIC` | Float 0.0-1.0 | `0.95` |
| `CATEGORICAL` | String labels | `"correct"`, `"incorrect"` |
| `BOOLEAN` | True/False | `True` |

## Key Methods

| Method | Purpose |
|--------|---------|
| `start_as_current_observation()` | Context manager for spans |
| `create_score()` | Add evaluation score |
| `get_prompt()` | Fetch versioned prompt |
| `prompt.compile()` | Render template variables |

## Cost Tracking

| Model Family | Auto-Tokenizer | Auto-Cost |
|--------------|----------------|-----------|
| OpenAI GPT | Yes | Yes |
| Anthropic Claude | Yes | Yes |
| Google Gemini | Yes | Yes |
| Custom Models | Configure | Configure |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Track LLM call | `as_type="generation"` |
| Track function | `as_type="span"` |
| Group conversation | Use `session_id` |
| Link across services | Share `trace_id` |

## Common Pitfalls

| Do Not | Do |
|--------|-----|
| Forget `flush()` in Lambda/Cloud Run | Call `langfuse.flush()` before exit |
| Hardcode prompts | Use `get_prompt()` with labels |
| Skip user_id | Track users for analytics |
| Ignore costs | Set up cost alerting |

## Related Documentation

| Topic | Path |
|-------|------|
| SDK Setup | `patterns/python-sdk-integration.md` |
| Full Index | `index.md` |
