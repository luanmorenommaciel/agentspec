# Structured JSON Output Pattern

> **Purpose**: Guarantee valid JSON responses matching a defined schema
> **MCP Validated**: 2026-01-25

## When to Use

- Extracting data that feeds into databases
- Building APIs that return structured responses
- Ensuring consistent output format across requests
- Validating extracted data at API level

## Implementation

```python
from google import genai
from google.genai import types
import json
from typing import TypedDict, List, Optional
from pydantic import BaseModel


class LineItem(BaseModel):
    """Pydantic model for line item validation."""
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: float


class Invoice(BaseModel):
    """Pydantic model for invoice validation."""
    invoice_id: str
    vendor_name: str
    invoice_date: str
    total_amount: float
    line_items: List[LineItem] = []


def create_json_schema_from_pydantic(model: type[BaseModel]) -> dict:
    """Convert Pydantic model to JSON Schema for Gemini."""
    return model.model_json_schema()


class StructuredExtractor:
    """Extract data with guaranteed JSON schema compliance."""

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )

    def extract_with_schema(
        self,
        prompt: str,
        content: types.Content,
        schema: dict,
        model: str = "gemini-2.5-flash"
    ) -> dict:
        """Extract data matching the provided JSON schema."""

        response = self.client.models.generate_content(
            model=model,
            contents=[
                types.Content(parts=[types.Part(text=prompt)]),
                content
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.2,
            )
        )

        # Parse and return
        return json.loads(response.text)

    def extract_invoice(self, image_content: types.Content) -> Invoice:
        """Extract invoice with Pydantic validation."""
        schema = create_json_schema_from_pydantic(Invoice)

        raw_data = self.extract_with_schema(
            prompt="Extract all invoice information from this document.",
            content=image_content,
            schema=schema
        )

        # Validate with Pydantic
        return Invoice(**raw_data)


# Using with Pydantic models (recommended)
def extract_validated(extractor: StructuredExtractor, image_path: str) -> Invoice:
    """Extract and validate invoice data."""
    import base64

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    content = types.Content(
        parts=[
            types.Part(
                inline_data=types.Blob(mime_type="image/png", data=image_data)
            )
        ]
    )

    return extractor.extract_invoice(content)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `response_mime_type` | `"application/json"` | Required for JSON mode |
| `response_schema` | JSON Schema dict | Defines output structure |
| `temperature` | `0.2` | Low for consistent structure |

## Schema Best Practices

```python
# DO: Use required fields for critical data
good_schema = {
    "type": "object",
    "properties": {
        "invoice_id": {"type": "string"},
        "total": {"type": "number"}
    },
    "required": ["invoice_id", "total"]  # Ensures these are always present
}

# DO: Add descriptions for clarity
better_schema = {
    "type": "object",
    "properties": {
        "invoice_date": {
            "type": "string",
            "description": "Invoice date in YYYY-MM-DD format"
        }
    }
}

# DON'T: Duplicate schema in prompt
# The schema should only be in response_schema, not repeated in text
```

## Example Usage

```python
extractor = StructuredExtractor(project_id="my-project")

# With Pydantic validation
invoice = extract_validated(extractor, "invoice.png")
print(f"Vendor: {invoice.vendor_name}")
print(f"Total: ${invoice.total_amount:.2f}")

# Direct schema usage
custom_schema = {
    "type": "object",
    "properties": {"total": {"type": "number"}},
    "required": ["total"]
}
result = extractor.extract_with_schema(
    prompt="Extract the total amount.",
    content=image_content,
    schema=custom_schema
)
```

## See Also

- [invoice-extraction.md](invoice-extraction.md)
- [../concepts/structured-output.md](../concepts/structured-output.md)
