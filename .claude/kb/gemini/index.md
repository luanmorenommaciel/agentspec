# Gemini Knowledge Base

> **Purpose**: Google's multimodal LLM for document extraction and vision tasks
> **MCP Validated**: 2026-01-25

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/model-capabilities.md](concepts/model-capabilities.md) | Gemini model variants and capabilities |
| [concepts/vertex-ai-integration.md](concepts/vertex-ai-integration.md) | Vertex AI SDK and authentication |
| [concepts/multimodal-prompting.md](concepts/multimodal-prompting.md) | Text + image input patterns |
| [concepts/token-limits-pricing.md](concepts/token-limits-pricing.md) | Context windows and cost management |
| [concepts/structured-output.md](concepts/structured-output.md) | JSON schema and responseSchema |
| [concepts/safety-settings.md](concepts/safety-settings.md) | Harm categories and thresholds |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/invoice-extraction.md](patterns/invoice-extraction.md) | Extract structured data from invoices |
| [patterns/structured-json-output.md](patterns/structured-json-output.md) | Enforce JSON schema responses |
| [patterns/openrouter-fallback.md](patterns/openrouter-fallback.md) | Multi-provider resilience |
| [patterns/batch-processing.md](patterns/batch-processing.md) | High-volume document processing |
| [patterns/error-handling-retries.md](patterns/error-handling-retries.md) | Robust API error handling |
| [patterns/prompt-versioning.md](patterns/prompt-versioning.md) | Version control for prompts |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Multimodal Input** | Process text, images, PDFs, video in single request |
| **Structured Output** | responseSchema guarantees JSON adherence |
| **Vision OCR** | Native document understanding without separate OCR |
| **Safety Filters** | Configurable harm category thresholds |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/model-capabilities.md, concepts/vertex-ai-integration.md |
| **Intermediate** | patterns/invoice-extraction.md, patterns/structured-json-output.md |
| **Advanced** | patterns/batch-processing.md, patterns/error-handling-retries.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| python-developer | patterns/invoice-extraction.md | Implement extraction logic |
| test-generator | patterns/error-handling-retries.md | Test error scenarios |

---

## Important Notes

- **Model Deprecation**: Gemini 1.5 Flash/Pro retired. Use Gemini 2.5+ models.
- **SDK Migration**: vertexai.generative_models deprecated June 2025. Use google-genai SDK.
- **Invoice Accuracy**: Gemini achieves 94% accuracy on scanned invoices.
