# Custom Validators Pattern

> **Purpose**: Business rule validation for invoice extraction with custom logic
> **MCP Validated**: 2026-01-25

## When to Use

- Enforcing business rules beyond type validation
- Cross-field validation (e.g., date ranges, total calculations)
- Normalizing and transforming extracted data

## Implementation

```python
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
from typing import Optional, Any
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing_extensions import Self
import re

class VendorType(str, Enum):
    UBEREATS = "ubereats"
    DOORDASH = "doordash"
    OTHER = "other"

VENDOR_PATTERNS = {
    VendorType.UBEREATS: [r"uber\s*eats", r"uber"],
    VendorType.DOORDASH: [r"door\s*dash", r"doordash"],
}

class InvoiceWithValidation(BaseModel):
    invoice_id: str
    vendor_name: str
    vendor_type: VendorType = VendorType.OTHER
    invoice_date: date
    due_date: Optional[date] = None
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    currency: str = "USD"

    @field_validator("invoice_id", mode="after")
    @classmethod
    def normalize_invoice_id(cls, v: str) -> str:
        v = v.strip().upper()
        v = re.sub(r"^(INVOICE|INV|#)\s*[-:]?\s*", "INV-", v)
        return v

    @field_validator("vendor_name", mode="before")
    @classmethod
    def clean_vendor_name(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = " ".join(v.split()).title()
        return v

    @field_validator("currency", mode="after")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in {"USD", "EUR", "GBP", "CAD"}:
            raise ValueError(f"Unsupported currency: {v}")
        return v

    @field_validator("subtotal", "tax_amount", "total_amount", mode="after")
    @classmethod
    def round_money(cls, v: Decimal) -> Decimal:
        return round(v, 2)

    @model_validator(mode="after")
    def auto_classify_vendor(self) -> Self:
        if self.vendor_type == VendorType.OTHER:
            name_lower = self.vendor_name.lower()
            for vtype, patterns in VENDOR_PATTERNS.items():
                if any(re.search(p, name_lower) for p in patterns):
                    self.vendor_type = vtype
                    break
        return self

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        today = date.today()
        if self.invoice_date > today:
            raise ValueError("Invoice date cannot be in the future")
        if self.invoice_date < today - timedelta(days=365):
            raise ValueError("Invoice date is more than 1 year old")
        if self.due_date and self.due_date < self.invoice_date:
            raise ValueError("Due date must be after invoice date")
        return self

    @model_validator(mode="after")
    def validate_totals(self) -> Self:
        expected = self.subtotal + self.tax_amount
        if abs(self.total_amount - expected) > Decimal("0.02"):
            pass  # Log warning but allow
        return self
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `tolerance` | `0.02` | Allowed difference in monetary calculations |
| `max_invoice_age` | `365 days` | Maximum age for valid invoices |

## Example Usage

```python
data = {
    "invoice_id": "invoice #12345",
    "vendor_name": "uber eats restaurant",
    "vendor_type": "other",
    "invoice_date": "2024-01-15",
    "subtotal": "100.005",
    "tax_amount": "8.00",
    "total_amount": "108.01",
}

invoice = InvoiceWithValidation.model_validate(data)
print(invoice.invoice_id)   # "INV-12345"
print(invoice.vendor_name)  # "Uber Eats Restaurant"
print(invoice.vendor_type)  # VendorType.UBEREATS

# Context-aware validation
class ContextAwareInvoice(BaseModel):
    vendor_name: str

    @field_validator("vendor_name", mode="after")
    @classmethod
    def validate_known_vendor(cls, v: str, info: ValidationInfo) -> str:
        context = info.context or {}
        known = context.get("known_vendors", [])
        if known and v not in known:
            raise ValueError(f"Unknown vendor: {v}")
        return v

# Usage with context
invoice = ContextAwareInvoice.model_validate(
    {"vendor_name": "UberEats"},
    context={"known_vendors": ["UberEats", "DoorDash"]}
)
```

## See Also

- [validators.md](../concepts/validators.md)
- [llm-output-validation.md](llm-output-validation.md)
- [error-handling.md](error-handling.md)
