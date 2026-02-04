# Error Handling Pattern

> **Purpose**: Handle ValidationError and recover from malformed LLM responses
> **MCP Validated**: 2026-01-25

## When to Use

- Catching and processing Pydantic ValidationError exceptions
- Logging validation failures for debugging
- Graceful degradation when LLM output is partially valid

## Implementation

```python
from pydantic import BaseModel, Field, ValidationError
from typing import Optional
from datetime import date
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)

class InvoiceSchema(BaseModel):
    invoice_id: str
    vendor_name: str
    invoice_date: date
    total_amount: Decimal = Field(..., ge=0)

class ValidationResult:
    def __init__(self, success: bool, data: Optional[BaseModel] = None,
                 errors: Optional[list[dict]] = None, raw_input: Optional[str] = None):
        self.success = success
        self.data = data
        self.errors = errors or []
        self.raw_input = raw_input

    @property
    def error_summary(self) -> str:
        if not self.errors:
            return ""
        return "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in self.errors)

def validate_with_recovery(
    json_input: str,
    model_class: type[BaseModel],
    fallback_values: Optional[dict] = None
) -> ValidationResult:
    fallback_values = fallback_values or {}

    # Step 1: Parse JSON
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return ValidationResult(
            success=False,
            errors=[{"loc": ("__root__",), "msg": f"Invalid JSON: {e}", "type": "json_invalid"}],
            raw_input=json_input
        )

    # Step 2: Validate
    try:
        validated = model_class.model_validate(data)
        return ValidationResult(success=True, data=validated)
    except ValidationError as e:
        errors = e.errors()
        logger.warning(f"Validation failed: {errors}")

        # Step 3: Attempt recovery
        if fallback_values:
            recovered = _apply_fallbacks(data, errors, fallback_values)
            try:
                validated = model_class.model_validate(recovered)
                return ValidationResult(success=True, data=validated, errors=errors)
            except ValidationError as e2:
                errors = e2.errors()

        return ValidationResult(success=False, errors=errors, raw_input=json_input)

def _apply_fallbacks(data: dict, errors: list[dict], fallbacks: dict) -> dict:
    result = data.copy()
    error_fields = {e["loc"][0] for e in errors if e["loc"]}
    for field, default in fallbacks.items():
        if field in error_fields or field not in result:
            result[field] = default
    return result

def format_errors_for_logging(errors: list[dict]) -> dict:
    return {
        "error_count": len(errors),
        "fields": [{"location": ".".join(map(str, e["loc"])), "message": e["msg"],
                    "type": e["type"]} for e in errors]
    }

def format_errors_for_user(errors: list[dict]) -> str:
    if not errors:
        return "No errors"
    lines = ["Validation failed:"]
    for e in errors:
        loc = ".".join(map(str, e["loc"]))
        lines.append(f"  - {loc}: {e['msg']}")
    return "\n".join(lines)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `fallback_values` | `None` | Dict of field defaults for recovery |
| Logging level | `WARNING` | Log level for validation failures |

## Example Usage

```python
# Basic validation
result = validate_with_recovery(json_input=llm_response, model_class=InvoiceSchema)

if result.success:
    invoice = result.data
else:
    logger.error("Validation failed", extra=format_errors_for_logging(result.errors))

# With fallback recovery
result = validate_with_recovery(
    json_input=llm_response,
    model_class=InvoiceSchema,
    fallback_values={"vendor_name": "Unknown Vendor", "total_amount": Decimal("0")}
)

# Direct ValidationError handling
try:
    invoice = InvoiceSchema.model_validate_json(llm_response)
except ValidationError as e:
    for error in e.errors():
        print(f"Field: {error['loc']}, Error: {error['msg']}")
    error_json = e.json()
```

## See Also

- [llm-output-validation.md](llm-output-validation.md)
- [validators.md](../concepts/validators.md)
- [custom-validators.md](custom-validators.md)
