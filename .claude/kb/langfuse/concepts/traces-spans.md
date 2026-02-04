# Traces and Spans

> **Purpose**: Hierarchical structure for observability data in Langfuse
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

A trace represents a single request or operation in your LLM application. Traces contain observations (spans, generations, events) that form a hierarchical tree showing the execution flow. Sessions optionally group multiple traces together, useful for multi-turn conversations.

## The Pattern

```python
from langfuse import get_client

langfuse = get_client()

# Create a trace with context manager
with langfuse.start_as_current_observation(
    as_type="span",
    name="process-invoice",
    user_id="user-123",
    session_id="session-456",
    metadata={"source": "cloud-run"}
) as root_span:

    # Nested span for preprocessing
    with langfuse.start_as_current_observation(
        as_type="span",
        name="preprocess"
    ) as preprocess_span:
        preprocess_span.update(output="Preprocessed invoice image")

    # Nested generation for LLM call
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="extract-fields",
        model="gemini-1.5-pro"
    ) as gen:
        gen.update(output={"vendor": "UberEats", "total": 42.50})

    root_span.update(output="Invoice processed successfully")
```

## Quick Reference

| Component | Description | Use Case |
|-----------|-------------|----------|
| `trace` | Root container | Single request lifecycle |
| `span` | Generic observation | Function calls, I/O operations |
| `generation` | LLM-specific span | Model calls with tokens/cost |
| `event` | Point-in-time marker | Logging discrete events |
| `session` | Trace grouping | Chat threads, user sessions |

## Common Mistakes

### Wrong

```python
# Creating orphan spans without context
span = langfuse.start_span(name="my-span")
# Forgetting to end it or losing the hierarchy
```

### Correct

```python
# Using context manager ensures proper hierarchy and cleanup
with langfuse.start_as_current_observation(
    as_type="span",
    name="my-span"
) as span:
    # Automatic parent-child relationship
    # Automatic end() on exit
    span.update(output="Done")
```

## Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `trace_id` | string | Unique identifier for the trace |
| `user_id` | string | End-user identifier |
| `session_id` | string | Groups related traces |
| `metadata` | dict | Custom key-value pairs |
| `input` | any | Operation input data |
| `output` | any | Operation output data |

## Related

- [Generations](../concepts/generations.md)
- [Python SDK Integration](../patterns/python-sdk-integration.md)
- [Trace Linking](../patterns/trace-linking.md)
