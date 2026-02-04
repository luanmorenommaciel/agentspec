# Batch Processing Pattern

> **Purpose**: Process high volumes of documents efficiently
> **MCP Validated**: 2026-01-25

## When to Use

- Processing 100+ invoices in a batch
- Nightly ETL jobs for document extraction
- Cost-optimized bulk operations
- Parallel processing requirements

## Implementation

```python
from google import genai
from google.genai import types
import asyncio
import base64
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    file_path: str
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class BatchInvoiceProcessor:
    """Process large batches of invoices with rate limiting and retries."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        max_concurrent: int = 10,
        model: str = "gemini-2.5-flash-lite"  # Cost-optimized for batch
    ):
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        self.model = model
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

        self.schema = {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string"},
                "vendor_name": {"type": "string"},
                "invoice_date": {"type": "string"},
                "total_amount": {"type": "number"},
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "total": {"type": "number"}
                        }
                    }
                }
            },
            "required": ["invoice_id", "vendor_name", "total_amount"]
        }

    async def process_batch(self, file_paths: List[str]) -> List[BatchResult]:
        """Process a batch of invoice files."""
        tasks = [self._process_single(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        batch_results = []
        for path, result in zip(file_paths, results):
            if isinstance(result, Exception):
                batch_results.append(BatchResult(
                    file_path=path,
                    success=False,
                    error=str(result)
                ))
            else:
                batch_results.append(result)

        return batch_results

    async def _process_single(self, file_path: str) -> BatchResult:
        """Process a single file with rate limiting."""
        async with self.semaphore:
            try:
                # Run sync extraction in thread pool
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None,
                    self._extract_sync,
                    file_path
                )
                return BatchResult(file_path=file_path, success=True, data=data)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                return BatchResult(file_path=file_path, success=False, error=str(e))

    def _extract_sync(self, file_path: str) -> dict:
        """Synchronous extraction (runs in thread pool)."""
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        mime_type = self._get_mime_type(file_path)

        content = types.Content(
            parts=[
                types.Part(text="Extract all invoice information."),
                types.Part(
                    inline_data=types.Blob(mime_type=mime_type, data=image_data)
                )
            ]
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=[content],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=self.schema,
                temperature=0.2
            )
        )

        return json.loads(response.text)

    def _get_mime_type(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        return {".png": "image/png", ".tiff": "image/tiff", ".jpg": "image/jpeg"
               }.get(suffix, "image/png")


async def run_batch(invoice_dir: str, project_id: str):
    """Example: Process all invoices in a directory."""
    processor = BatchInvoiceProcessor(project_id=project_id, max_concurrent=10)

    files = list(Path(invoice_dir).glob("*.png")) + \
            list(Path(invoice_dir).glob("*.tiff"))

    logger.info(f"Processing {len(files)} invoices...")
    results = await processor.process_batch([str(f) for f in files])

    success = sum(1 for r in results if r.success)
    logger.info(f"Completed: {success}/{len(results)} successful")

    return results
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `model` | `gemini-2.5-flash-lite` | Lowest cost for batch |
| `max_concurrent` | 10 | Parallel requests |
| `temperature` | 0.2 | Consistent extraction |

## Example Usage

```python
import asyncio

results = asyncio.run(run_batch(
    invoice_dir="/data/invoices",
    project_id="my-gcp-project"
))

# Save results
for r in results:
    if r.success:
        print(f"{r.file_path}: ${r.data['total_amount']}")
    else:
        print(f"{r.file_path}: FAILED - {r.error}")
```

## See Also

- [invoice-extraction.md](invoice-extraction.md)
- [error-handling-retries.md](error-handling-retries.md)
- [../concepts/token-limits-pricing.md](../concepts/token-limits-pricing.md)
