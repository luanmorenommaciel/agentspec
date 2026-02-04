# Pydantic Knowledge Base

> **Purpose**: Python data validation library for LLM output parsing and structured extraction
> **MCP Validated**: 2026-01-25

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/base-model.md](concepts/base-model.md) | BaseModel fundamentals and Field configuration |
| [concepts/field-types.md](concepts/field-types.md) | Type hints, Enums, Literals, and Optional fields |
| [concepts/validators.md](concepts/validators.md) | field_validator and model_validator decorators |
| [concepts/nested-models.md](concepts/nested-models.md) | Composing models for complex structures |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/llm-output-validation.md](patterns/llm-output-validation.md) | Validating LLM JSON responses |
| [patterns/extraction-schema.md](patterns/extraction-schema.md) | Invoice extraction schema definition |
| [patterns/error-handling.md](patterns/error-handling.md) | ValidationError handling and recovery |
| [patterns/custom-validators.md](patterns/custom-validators.md) | Business rule validation logic |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/invoice-schema.yaml](specs/invoice-schema.yaml) | Invoice extraction JSON schema |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **BaseModel** | Core class for data models with automatic validation |
| **Field** | Configure defaults, constraints, and metadata |
| **Validators** | Custom validation logic via decorators |
| **Type Coercion** | Automatic conversion (e.g., "123" to int) |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/base-model.md, concepts/field-types.md |
| **Intermediate** | patterns/extraction-schema.md, patterns/error-handling.md |
| **Advanced** | patterns/llm-output-validation.md, patterns/custom-validators.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| python-developer | patterns/extraction-schema.md | Define invoice models |
| test-generator | patterns/error-handling.md | Test validation edge cases |

---

## Project Context

This KB supports the GenAI Invoice Processing Pipeline:
- Validating Gemini's JSON extraction output
- Defining invoice extraction schema
- Type coercion and default values
- Error handling for malformed LLM responses
