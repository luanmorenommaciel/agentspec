# Invoice Extraction Pattern

> **Purpose**: Extract structured data from invoice images using Gemini vision
> **MCP Validated**: 2026-01-25

## When to Use

- Processing TIFF/PNG invoice images
- Extracting vendor, line items, totals from documents
- Building automated invoice intelligence pipelines
- Replacing manual data entry workflows

## Implementation

```python
from google import genai
from google.genai import types
import base64
import json
from pathlib import Path


class InvoiceExtractor:
    """Extract structured data from invoice images using Gemini."""

    INVOICE_SCHEMA = {
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string", "description": "Unique invoice number"},
            "vendor_name": {"type": "string", "description": "Restaurant or vendor name"},
            "vendor_address": {"type": "string"},
            "invoice_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
            "due_date": {"type": "string"},
            "subtotal": {"type": "number"},
            "tax_amount": {"type": "number"},
            "total_amount": {"type": "number", "description": "Final amount due"},
            "currency": {"type": "string", "default": "USD"},
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit_price": {"type": "number"},
                        "total": {"type": "number"}
                    },
                    "required": ["description", "total"]
                }
            }
        },
        "required": ["invoice_id", "vendor_name", "invoice_date", "total_amount"]
    }

    EXTRACTION_PROMPT = """Extract all invoice information from this document image.

Instructions:
- Extract the invoice number, vendor details, dates, and all line items
- Convert dates to YYYY-MM-DD format
- Extract numeric values without currency symbols
- If a field is not visible, omit it from the response
- For line items, include description, quantity, unit price, and line total"""

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        self.model = "gemini-2.5-flash"

    def extract(self, image_path: str) -> dict:
        """Extract invoice data from an image file."""
        # Load and encode image
        image_data = self._load_image(image_path)
        mime_type = self._get_mime_type(image_path)

        # Build request
        content = types.Content(
            parts=[
                types.Part(text=self.EXTRACTION_PROMPT),
                types.Part(
                    inline_data=types.Blob(
                        mime_type=mime_type,
                        data=image_data
                    )
                )
            ]
        )

        # Generate with structured output
        response = self.client.models.generate_content(
            model=self.model,
            contents=[content],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=self.INVOICE_SCHEMA,
                temperature=0.3,  # Low temp for accuracy
            )
        )

        return json.loads(response.text)

    def _load_image(self, path: str) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_mime_type(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".webp": "image/webp",
        }.get(suffix, "image/png")
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `model` | `gemini-2.5-flash` | Best cost/quality for invoices |
| `temperature` | `0.3` | Low for consistent extraction |
| `response_mime_type` | `application/json` | Enable structured output |

## Example Usage

```python
extractor = InvoiceExtractor(project_id="my-gcp-project")

result = extractor.extract("invoices/ubereats-001.tiff")
print(result)
# {
#   "invoice_id": "INV-2026-001",
#   "vendor_name": "Joe's Pizza",
#   "invoice_date": "2026-01-20",
#   "total_amount": 45.99,
#   "line_items": [...]
# }
```

## See Also

- [structured-json-output.md](structured-json-output.md)
- [batch-processing.md](batch-processing.md)
- [../concepts/multimodal-prompting.md](../concepts/multimodal-prompting.md)
