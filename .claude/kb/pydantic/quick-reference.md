# Pydantic Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-01-25

## Core Classes

| Class | Import | Purpose |
|-------|--------|---------|
| `BaseModel` | `from pydantic import BaseModel` | Base class for all models |
| `Field` | `from pydantic import Field` | Configure field constraints |
| `ValidationError` | `from pydantic import ValidationError` | Validation exception |

## Field Types

| Type | Example | Notes |
|------|---------|-------|
| `str` | `name: str` | Required string |
| `int` | `count: int` | Auto-coerces "123" |
| `float` | `amount: float` | Auto-coerces from int/str |
| `bool` | `active: bool` | Coerces 1/0, "true"/"false" |
| `date` | `invoice_date: date` | ISO format string coercion |
| `Optional[T]` | `tax: Optional[float] = None` | Nullable with default |
| `list[T]` | `items: list[Item]` | Typed list |
| `Literal` | `status: Literal["a","b"]` | Constrained values |
| `Enum` | `vendor: VendorType` | Enum class values |

## Validator Decorators

| Decorator | Mode | Use Case |
|-----------|------|----------|
| `@field_validator` | `after` | Validate parsed value |
| `@field_validator` | `before` | Transform raw input |
| `@field_validator` | `wrap` | Control validation flow |
| `@model_validator` | `after` | Cross-field validation |
| `@model_validator` | `before` | Pre-process input dict |

## Validation Methods

| Method | Input | Output |
|--------|-------|--------|
| `Model(**data)` | dict | Model instance |
| `Model.model_validate(obj)` | dict/object | Model instance |
| `Model.model_validate_json(json_str)` | JSON string | Model instance |
| `Model.model_dump()` | - | dict |
| `Model.model_dump_json()` | - | JSON string |
| `Model.model_json_schema()` | - | JSON Schema dict |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Parse LLM JSON response | `model_validate_json()` |
| Validate dict from API | `model_validate()` |
| Export for logging | `model_dump()` |
| Generate prompt schema | `model_json_schema()` |

## Common Pitfalls

| Do Not | Do Instead |
|--------|------------|
| Raise `ValidationError` in validators | Raise `ValueError` |
| Ignore validation errors | Wrap in try/except, log details |
| Use bare `dict` for nested data | Define nested `BaseModel` |
| Hardcode enum values | Use `Enum` or `Literal` |

## Related Documentation

| Topic | Path |
|-------|------|
| BaseModel Details | `concepts/base-model.md` |
| LLM Validation | `patterns/llm-output-validation.md` |
| Full Index | `index.md` |
