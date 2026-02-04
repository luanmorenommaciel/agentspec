# Validators

> **Purpose**: Custom validation logic using field_validator and model_validator
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Pydantic provides `@field_validator` for single-field validation and `@model_validator`
for cross-field validation. Validators run in modes: `before` (pre-coercion), `after`
(post-coercion), or `wrap` (full control). Raise `ValueError` for validation failures.

## The Pattern

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self
from datetime import date

class Invoice(BaseModel):
    invoice_id: str
    invoice_date: date
    due_date: date
    subtotal: float
    tax_amount: float
    total_amount: float

    @field_validator("invoice_id", mode="after")
    @classmethod
    def validate_invoice_id(cls, v: str) -> str:
        if not v.startswith("INV-"):
            raise ValueError("Invoice ID must start with 'INV-'")
        return v.upper()

    @model_validator(mode="after")
    def validate_dates_and_totals(self) -> Self:
        if self.due_date < self.invoice_date:
            raise ValueError("Due date cannot be before invoice date")
        expected = round(self.subtotal + self.tax_amount, 2)
        if abs(self.total_amount - expected) > 0.01:
            raise ValueError(f"Total mismatch: {self.total_amount} != {expected}")
        return self
```

## Quick Reference

| Decorator | Mode | Input Type | Use Case |
|-----------|------|------------|----------|
| `@field_validator` | `after` | Parsed type | Validate coerced value |
| `@field_validator` | `before` | `Any` | Transform raw input |
| `@field_validator` | `wrap` | `Any` | Control flow |
| `@model_validator` | `after` | `Self` | Cross-field checks |
| `@model_validator` | `before` | `dict` | Pre-process input |

## Field Validator Modes

```python
from pydantic import field_validator
from typing import Any

# AFTER: Runs after type coercion (type-safe)
@field_validator("amount", mode="after")
@classmethod
def check_positive(cls, v: float) -> float:
    if v < 0:
        raise ValueError("Amount must be positive")
    return v

# BEFORE: Runs before coercion (raw input)
@field_validator("phone", mode="before")
@classmethod
def clean_phone(cls, v: Any) -> Any:
    if isinstance(v, str):
        return v.replace("-", "").replace(" ", "")
    return v
```

## Model Validator

```python
from pydantic import model_validator
from typing_extensions import Self

@model_validator(mode="after")
def check_consistency(self) -> Self:
    """Cross-field validation after all fields parsed."""
    if self.end_date < self.start_date:
        raise ValueError("end_date must be after start_date")
    return self

@model_validator(mode="before")
@classmethod
def preprocess(cls, data: dict) -> dict:
    """Transform input dict before field parsing."""
    if "full_name" in data:
        parts = data["full_name"].split()
        data["first_name"] = parts[0]
        data["last_name"] = " ".join(parts[1:])
    return data
```

## Common Mistakes

### Wrong

```python
@field_validator("amount")
@classmethod
def check_amount(cls, v):
    # DON'T raise ValidationError directly
    raise ValidationError("Invalid")
```

### Correct

```python
@field_validator("amount")
@classmethod
def check_amount(cls, v: float) -> float:
    # Raise ValueError - Pydantic wraps it
    if v < 0:
        raise ValueError("Amount must be non-negative")
    return v
```

## Multiple Fields

```python
@field_validator("subtotal", "tax_amount", "total_amount", mode="after")
@classmethod
def round_money(cls, v: float) -> float:
    return round(v, 2)

# Wildcard for all fields
@field_validator("*", mode="before")
@classmethod
def strip_strings(cls, v: Any) -> Any:
    if isinstance(v, str):
        return v.strip()
    return v
```

## Related

- [base-model.md](base-model.md)
- [custom-validators.md](../patterns/custom-validators.md)
- [error-handling.md](../patterns/error-handling.md)
