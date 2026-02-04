# Nested Models

> **Purpose**: Composing BaseModel classes for complex, hierarchical data structures
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Pydantic supports nested models where one BaseModel contains another as a field type.
This enables validation of complex structures like invoices with line items. Nested
models are validated recursively, and JSON Schema generation includes all nested definitions.

## The Pattern

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal
from enum import Enum

class VendorType(str, Enum):
    UBEREATS = "ubereats"
    DOORDASH = "doordash"
    OTHER = "other"

class LineItem(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., ge=0)
    amount: Decimal = Field(..., ge=0)

class Invoice(BaseModel):
    invoice_id: str
    vendor_type: VendorType
    invoice_date: date
    line_items: list[LineItem] = Field(default_factory=list)
    total_amount: Decimal
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `{"line_items": [{"..."}]}` | `Invoice(line_items=[LineItem(...)])` | Dict to nested |
| `invoice.line_items[0].amount` | `Decimal` | Access list item |

## Instantiation

```python
data = {
    "invoice_id": "INV-001",
    "vendor_type": "ubereats",
    "invoice_date": "2024-01-15",
    "line_items": [
        {"description": "Delivery", "quantity": 1, "unit_price": "2.99", "amount": "2.99"}
    ],
    "total_amount": "3.24"
}
invoice = Invoice.model_validate(data)

# From JSON string
invoice = Invoice.model_validate_json(json_string)
```

## Lists of Nested Models

```python
line_items: list[LineItem]  # Type hint

for item in invoice.line_items:
    print(f"{item.description}: {item.amount}")

# Default empty list
line_items: list[LineItem] = Field(default_factory=list)
```

## Common Mistakes

### Wrong

```python
class Invoice(BaseModel):
    line_items: list[dict]  # No validation inside!
```

### Correct

```python
class Invoice(BaseModel):
    line_items: list[LineItem]  # Full validation
```

## Validation Cascade

```python
try:
    Invoice.model_validate({"line_items": [{"quantity": -1}]})
except ValidationError as e:
    # Error location: "line_items.0.quantity"
    for error in e.errors():
        print(error["loc"], error["msg"])
```

## Related

- [base-model.md](base-model.md)
- [field-types.md](field-types.md)
- [extraction-schema.md](../patterns/extraction-schema.md)
