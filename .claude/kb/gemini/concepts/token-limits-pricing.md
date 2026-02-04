# Token Limits and Pricing

> **Purpose**: Understand context windows and manage costs
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Gemini models offer generous context windows (up to 1M tokens) with competitive pricing. Understanding token consumption helps optimize costs for high-volume document processing.

## Pricing Table (January 2026)

| Model | Input/1M Tokens | Output/1M Tokens | Context |
|-------|-----------------|------------------|---------|
| gemini-2.5-flash-lite | $0.10 | $0.40 | 1M |
| gemini-2.5-flash | $0.15 | $0.60 | 1M |
| gemini-2.5-pro | $1.25 | $5.00 | 1M |
| gemini-3-pro-preview | $2.00 | $12.00 | 1M |

## Token Limits

| Model | Max Input | Max Output |
|-------|-----------|------------|
| All 2.5+ models | 1,000,000 | 64,000 |

## Token Consumption by Content Type

```python
# Approximate token counts
token_estimates = {
    "text_1k_chars": 250,        # ~250 tokens per 1K characters
    "image_standard": 258,       # Base image cost
    "image_high_res": 1290,      # 1024x1024 image
    "pdf_per_page": 258,         # Per page estimate
    "video_per_second": 258,     # At 1 fps
}
```

## Cost Calculator Example

```python
def estimate_cost(num_invoices: int, avg_pages: int = 2) -> dict:
    """Estimate cost for invoice processing batch."""
    # Using gemini-2.5-flash pricing
    INPUT_COST_PER_M = 0.15
    OUTPUT_COST_PER_M = 0.60

    # Estimates
    tokens_per_page = 258  # image tokens
    prompt_tokens = 500    # instruction tokens
    output_tokens = 1000   # JSON response

    total_input = num_invoices * (avg_pages * tokens_per_page + prompt_tokens)
    total_output = num_invoices * output_tokens

    input_cost = (total_input / 1_000_000) * INPUT_COST_PER_M
    output_cost = (total_output / 1_000_000) * OUTPUT_COST_PER_M

    return {
        "invoices": num_invoices,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "input_cost": f"${input_cost:.4f}",
        "output_cost": f"${output_cost:.4f}",
        "total_cost": f"${input_cost + output_cost:.4f}"
    }

# Example: 1000 invoices
print(estimate_cost(1000))
# {'invoices': 1000, 'input_tokens': 1016000, 'output_tokens': 1000000,
#  'input_cost': '$0.1524', 'output_cost': '$0.6000', 'total_cost': '$0.7524'}
```

## Quick Reference

| Batch Size | Est. Cost (2.5-flash) | Est. Cost (2.5-flash-lite) |
|------------|----------------------|---------------------------|
| 100 invoices | $0.08 | $0.05 |
| 1,000 invoices | $0.75 | $0.50 |
| 10,000 invoices | $7.50 | $5.00 |

## Common Mistakes

### Wrong

```python
# Sending full-resolution images
# 4K image = ~5000+ tokens = unnecessary cost
```

### Correct

```python
# Resize images before sending
from PIL import Image
img = Image.open("invoice.png")
img.thumbnail((1024, 1024))  # Reduces to ~1290 tokens max
```

## Related

- [model-capabilities.md](model-capabilities.md)
- [../patterns/batch-processing.md](../patterns/batch-processing.md)
