# Safety Settings

> **Purpose**: Configure harm category thresholds for document processing
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Gemini includes configurable safety filters that can block content based on harm categories. For document extraction tasks, you may need to adjust these settings since invoices and business documents are typically safe content that might occasionally trigger false positives.

## Harm Categories

| Category | Description |
|----------|-------------|
| `HARM_CATEGORY_HATE_SPEECH` | Discriminatory content |
| `HARM_CATEGORY_HARASSMENT` | Bullying, threatening content |
| `HARM_CATEGORY_SEXUALLY_EXPLICIT` | Sexual content |
| `HARM_CATEGORY_DANGEROUS_CONTENT` | Harmful instructions |
| `HARM_CATEGORY_CIVIC_INTEGRITY` | Election-related misinformation |

## Block Thresholds

| Threshold | Blocks |
|-----------|--------|
| `BLOCK_NONE` | Nothing blocked (use carefully) |
| `BLOCK_ONLY_HIGH` | Only high probability |
| `BLOCK_MEDIUM_AND_ABOVE` | Medium and high probability |
| `BLOCK_LOW_AND_ABOVE` | Low, medium, and high probability |

**Default for Gemini 2.5+**: `BLOCK_NONE` (off)

## Configuration Example

```python
from google import genai
from google.genai import types

client = genai.Client(vertexai=True, project="my-project", location="us-central1")

# Configure safety for document extraction
safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
]

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[document_content],
    config=types.GenerateContentConfig(
        safety_settings=safety_settings
    )
)
```

## Handling Safety Blocks

```python
def extract_with_safety_check(content):
    """Extract data with safety block handling."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[content],
        config=types.GenerateContentConfig(
            safety_settings=safety_settings
        )
    )

    # Check if blocked
    if response.candidates[0].finish_reason == "SAFETY":
        blocked_categories = [
            rating.category
            for rating in response.candidates[0].safety_ratings
            if rating.blocked
        ]
        raise ValueError(f"Content blocked: {blocked_categories}")

    return response.text
```

## Recommended Settings for Invoice Processing

| Category | Setting | Reason |
|----------|---------|--------|
| Hate Speech | BLOCK_ONLY_HIGH | Invoices rarely contain |
| Harassment | BLOCK_ONLY_HIGH | Business documents safe |
| Sexually Explicit | BLOCK_MEDIUM_AND_ABOVE | Standard protection |
| Dangerous | BLOCK_ONLY_HIGH | Product names may trigger |

## Common Mistakes

### Wrong

```python
# Completely disabling safety without consideration
safety_settings = []  # No protection
```

### Correct

```python
# Relaxed but present settings for business documents
safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
]
```

## Related

- [model-capabilities.md](model-capabilities.md)
- [../patterns/error-handling-retries.md](../patterns/error-handling-retries.md)
