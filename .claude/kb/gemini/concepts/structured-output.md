# Structured Output

> **Purpose**: Generate guaranteed JSON responses with schema validation
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Gemini's Structured Outputs feature guarantees responses adhere to a specified JSON schema. This is essential for invoice extraction where consistent field names and types are required for downstream processing.

## Basic responseSchema Usage

```python
from google import genai
from google.genai import types

client = genai.Client(vertexai=True, project="my-project", location="us-central1")

# Define the schema
invoice_schema = {
    "type": "object",
    "properties": {
        "invoice_id": {"type": "string"},
        "vendor_name": {"type": "string"},
        "invoice_date": {"type": "string", "format": "date"},
        "total_amount": {"type": "number"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "unit_price": {"type": "number"},
                    "total": {"type": "number"}
                }
            }
        }
    },
    "required": ["invoice_id", "vendor_name", "total_amount"]
}

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image_content],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=invoice_schema
    )
)

# Response is guaranteed valid JSON matching schema
import json
data = json.loads(response.text)
```

## Quick Reference

| Config Key | Value | Purpose |
|------------|-------|---------|
| `response_mime_type` | `"application/json"` | Enable JSON mode |
| `response_schema` | JSON Schema object | Define structure |

## Supported JSON Schema Features (Gemini 2.5+)

| Feature | Support | Example |
|---------|---------|---------|
| Basic types | Yes | `string`, `number`, `integer`, `boolean` |
| Arrays | Yes | `{"type": "array", "items": {...}}` |
| Nested objects | Yes | `{"type": "object", "properties": {...}}` |
| Required fields | Yes | `"required": ["field1", "field2"]` |
| anyOf | Yes | Union types |
| $ref | Yes | Schema references |
| Enums | Yes | `{"enum": ["a", "b", "c"]}` |

## Best Practices

| Practice | Reason |
|----------|--------|
| Match schema order in prompts | Improves output quality |
| Use required fields | Ensures critical data extracted |
| Keep schemas focused | One document type per schema |
| Include descriptions | Helps model understand intent |

## Common Mistakes

### Wrong

```python
# Duplicating schema in prompt
prompt = """
Extract invoice data as JSON:
{"invoice_id": "...", "total": "..."}  # DON'T repeat schema here
"""
```

### Correct

```python
# Schema only in config, clear instruction in prompt
prompt = "Extract all invoice information from this document."
config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=invoice_schema  # Schema here only
)
```

## Related

- [multimodal-prompting.md](multimodal-prompting.md)
- [../patterns/structured-json-output.md](../patterns/structured-json-output.md)
