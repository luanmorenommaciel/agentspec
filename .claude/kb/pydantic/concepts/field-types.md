# Field Types

> **Purpose**: Type hints, Enums, Literals, and Optional fields for schema definition
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Pydantic uses Python type hints to define field types. It supports primitives,
complex types, Enums, Literals for constrained values, and Optional for nullable
fields. Type coercion happens automatically where possible.

## The Pattern

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum
from datetime import date
from decimal import Decimal

class VendorType(str, Enum):
    UBEREATS = "ubereats"
    DOORDASH = "doordash"
    GRUBHUB = "grubhub"
    OTHER = "other"

class LineItem(BaseModel):
    description: str
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., ge=0)
    amount: Decimal = Field(..., ge=0)

class Invoice(BaseModel):
    invoice_id: str
    vendor_name: str
    vendor_type: VendorType
    invoice_date: date
    due_date: Optional[date] = None
    currency: Literal["USD", "EUR", "GBP"] = "USD"
    line_items: list[LineItem] = Field(default_factory=list)
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `"ubereats"` | `VendorType.UBEREATS` | Enum coercion |
| `"2024-01-15"` | `date(2024, 1, 15)` | ISO date string |
| `"123.45"` | `Decimal("123.45")` | String to Decimal |
| `None` | `None` | Optional field |

## Primitive Types

```python
name: str                    # Required string
count: int                   # Coerces "123" to 123
amount: float                # Coerces int and string
active: bool                 # Coerces 1/0, "true"/"false"
price: Decimal               # Precise decimal math
```

## Optional and Default

```python
from typing import Optional

# Optional with None default
notes: Optional[str] = None

# Optional with value default
currency: str = "USD"

# Required (no default)
invoice_id: str

# Factory default for mutable types
items: list[str] = Field(default_factory=list)
```

## Enum Types

```python
from enum import Enum

class VendorType(str, Enum):
    """Inherit from str for JSON serialization."""
    UBEREATS = "ubereats"
    DOORDASH = "doordash"
    OTHER = "other"

# Usage in model
vendor_type: VendorType

# Accepts: "ubereats", VendorType.UBEREATS
```

## Literal Types

```python
from typing import Literal

# Constrained to specific values
status: Literal["pending", "paid", "cancelled"]
currency: Literal["USD", "EUR", "GBP"] = "USD"
```

## Common Mistakes

### Wrong

```python
# Mutable default - shared between instances!
items: list[str] = []
```

### Correct

```python
# Factory creates new list per instance
items: list[str] = Field(default_factory=list)
```

## Type Coercion Examples

```python
# All valid inputs for int field:
# 123 (int), "123" (str), 123.0 (float)

# All valid for date field:
# date(2024, 1, 15), "2024-01-15", datetime(2024, 1, 15)

# Enum accepts string value:
# "ubereats" -> VendorType.UBEREATS
```

## Related

- [base-model.md](base-model.md)
- [nested-models.md](nested-models.md)
- [extraction-schema.md](../patterns/extraction-schema.md)
