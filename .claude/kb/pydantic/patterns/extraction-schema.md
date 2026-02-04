# Extraction Schema Pattern

> **Purpose**: Define invoice extraction schemas for LLM prompting and output validation
> **MCP Validated**: 2026-01-25

## When to Use

- Defining structured output format for LLM extraction tasks
- Generating JSON Schema to include in LLM prompts
- Type-safe database insertion after extraction

## Implementation

```python
from pydantic import BaseModel, Field, computed_field, model_validator
from typing import Optional, Literal
from datetime import date
from decimal import Decimal
from enum import Enum
from typing_extensions import Self

class VendorType(str, Enum):
    UBEREATS = "ubereats"
    DOORDASH = "doordash"
    GRUBHUB = "grubhub"
    OTHER = "other"

class LineItem(BaseModel):
    description: str = Field(..., description="Item or service description", min_length=1)
    quantity: int = Field(default=1, description="Quantity of items", ge=1)
    unit_price: Decimal = Field(..., description="Price per unit", ge=0)
    amount: Decimal = Field(..., description="Total amount", ge=0)

class InvoiceSchema(BaseModel):
    """Invoice extraction schema for delivery platform invoices."""

    invoice_id: str = Field(..., description="Unique invoice identifier")
    vendor_name: str = Field(..., description="Restaurant or vendor name")
    vendor_type: VendorType = Field(default=VendorType.OTHER, description="Platform type")
    invoice_date: date = Field(..., description="Invoice issue date (YYYY-MM-DD)")
    due_date: Optional[date] = Field(default=None, description="Payment due date")
    subtotal: Decimal = Field(..., description="Subtotal before tax", ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), description="Tax amount", ge=0)
    commission_rate: Optional[Decimal] = Field(default=None, ge=0, le=1)
    commission_amount: Optional[Decimal] = Field(default=None, ge=0)
    total_amount: Decimal = Field(..., description="Total invoice amount", ge=0)
    currency: Literal["USD", "EUR", "GBP", "CAD"] = Field(default="USD")
    line_items: list[LineItem] = Field(default_factory=list)

    model_config = {
        "str_strip_whitespace": True,
        "validate_default": True,
        "json_schema_extra": {
            "examples": [{
                "invoice_id": "INV-2024-001",
                "vendor_name": "Pizza Palace",
                "vendor_type": "ubereats",
                "invoice_date": "2024-01-15",
                "subtotal": 100.00,
                "tax_amount": 8.00,
                "total_amount": 108.00,
                "currency": "USD",
                "line_items": []
            }]
        }
    }

    @computed_field
    @property
    def has_line_items(self) -> bool:
        return len(self.line_items) > 0

    @model_validator(mode="after")
    def validate_totals(self) -> Self:
        expected = self.subtotal + self.tax_amount
        if self.commission_amount:
            expected += self.commission_amount
        if abs(self.total_amount - expected) > Decimal("0.02"):
            pass  # Log warning but don't fail
        return self

def get_extraction_prompt_schema() -> str:
    """Generate JSON Schema string for LLM system prompt."""
    import json
    return json.dumps(InvoiceSchema.model_json_schema(), indent=2)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `str_strip_whitespace` | `True` | Auto-strip string fields |
| `validate_default` | `True` | Validate default values |

## Example Usage

```python
# 1. Generate schema for LLM prompt
schema_json = get_extraction_prompt_schema()

system_prompt = f"""
Extract invoice data from the image. Return valid JSON matching this schema:
{schema_json}
"""

# 2. Call LLM (e.g., Gemini)
llm_response = call_gemini(system_prompt, invoice_image)

# 3. Validate response
try:
    invoice = InvoiceSchema.model_validate_json(llm_response)
    print(f"Extracted: {invoice.vendor_name} - ${invoice.total_amount}")
except ValidationError as e:
    print(f"Extraction failed: {e.errors()}")
```

## See Also

- [llm-output-validation.md](llm-output-validation.md)
- [nested-models.md](../concepts/nested-models.md)
- [base-model.md](../concepts/base-model.md)
