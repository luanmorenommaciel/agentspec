# BaseModel

> **Purpose**: Core class for creating validated data models in Pydantic
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

BaseModel is the foundation of Pydantic. All models inherit from it to get automatic
validation, type coercion, and serialization. Define fields using Python type hints,
and Pydantic handles validation at instantiation.

## The Pattern

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class Invoice(BaseModel):
    """Invoice extraction model for LLM output validation."""

    invoice_id: str = Field(..., description="Unique invoice identifier")
    vendor_name: str = Field(..., min_length=1)
    invoice_date: date
    total_amount: float = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None

    model_config = {
        "str_strip_whitespace": True,
        "validate_default": True,
    }
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| `{"invoice_id": "INV-001", ...}` | `Invoice(...)` | Dict to model |
| `'{"invoice_id": "INV-001"}'` | `Invoice(...)` | JSON via `model_validate_json` |
| `invoice.model_dump()` | `dict` | Model to dict |
| `invoice.model_dump_json()` | `str` | Model to JSON string |

## Field Configuration

```python
from pydantic import Field

# Required field with description
invoice_id: str = Field(..., description="Unique ID")

# Optional with default
currency: str = Field(default="USD")

# Numeric constraints
amount: float = Field(..., ge=0, le=1000000)

# String constraints
name: str = Field(..., min_length=1, max_length=100)

# Alias for JSON key mapping
vendor: str = Field(..., alias="vendorName")
```

## Common Mistakes

### Wrong

```python
class Invoice(BaseModel):
    # Missing type hints - no validation!
    invoice_id = ""
    amount = 0.0
```

### Correct

```python
class Invoice(BaseModel):
    # Type hints enable validation
    invoice_id: str
    amount: float = Field(..., ge=0)
```

## Model Methods

```python
# Instantiation
invoice = Invoice(invoice_id="INV-001", vendor_name="Uber", ...)

# From dict
invoice = Invoice.model_validate({"invoice_id": "INV-001", ...})

# From JSON string (for LLM output)
invoice = Invoice.model_validate_json('{"invoice_id": "INV-001", ...}')

# To dict
data = invoice.model_dump()
data = invoice.model_dump(exclude_none=True)  # Skip None fields

# To JSON
json_str = invoice.model_dump_json(indent=2)

# JSON Schema (for LLM prompts)
schema = Invoice.model_json_schema()
```

## Related

- [field-types.md](field-types.md)
- [validators.md](validators.md)
- [extraction-schema.md](../patterns/extraction-schema.md)
