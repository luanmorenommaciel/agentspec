# Model Capabilities

> **Purpose**: Understand Gemini model variants and their capabilities
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Gemini is Google's multimodal LLM family capable of processing text, images, PDFs, video, and audio. For invoice extraction, the Flash variants offer the best cost-performance ratio with native vision capabilities that eliminate the need for separate OCR preprocessing.

## Model Hierarchy (January 2026)

```text
gemini-3-pro-preview     <- Cutting-edge (preview)
gemini-2.5-pro           <- Complex reasoning, highest quality
gemini-2.5-flash         <- Balanced speed/quality (recommended)
gemini-2.5-flash-lite    <- Highest throughput, lowest cost
```

**Note**: Gemini 1.5 and 2.0 models are deprecated. Update to 2.5+ immediately.

## Quick Reference

| Model | Context | Output Max | Use Case |
|-------|---------|------------|----------|
| `gemini-2.5-flash-lite` | 1M tokens | 64K | High-volume batch processing |
| `gemini-2.5-flash` | 1M tokens | 64K | Invoice extraction (primary) |
| `gemini-2.5-pro` | 1M tokens | 64K | Complex document analysis |

## Multimodal Capabilities

```python
# Supported input types
supported_inputs = [
    "text",           # Plain text prompts
    "image/*",        # PNG, JPEG, WEBP, HEIC, HEIF
    "application/pdf",# Native PDF understanding
    "video/*",        # MP4, MPEG, MOV, AVI, etc.
    "audio/*",        # WAV, MP3, AIFF, AAC, OGG, FLAC
]

# Image tokenization
# ~258-1290 tokens per image depending on resolution
# Higher resolution = more tokens
```

## Key Features for Document Extraction

| Feature | Description |
|---------|-------------|
| Native Vision | Process images without separate OCR |
| PDF Understanding | Extract text + interpret visual elements |
| Structured Output | Guarantee JSON schema adherence |
| Long Context | 1M token window for large documents |

## Common Mistakes

### Wrong

```python
# Using deprecated model names
model = "gemini-1.5-flash"  # DEPRECATED - returns 404
```

### Correct

```python
# Use current model names
model = "gemini-2.5-flash"  # Recommended for invoice extraction
```

## Performance Benchmarks

| Task | Gemini 2.5 | GPT-4V | Claude 3 |
|------|------------|--------|----------|
| Scanned invoice accuracy | 94% | 91% | 90% |
| Processing speed | Fast | Medium | Medium |
| Cost per 1K docs | $0.15 | $0.30 | $0.25 |

## Related

- [vertex-ai-integration.md](vertex-ai-integration.md)
- [multimodal-prompting.md](multimodal-prompting.md)
