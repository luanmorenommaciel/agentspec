# Prompt Versioning Pattern

> **Purpose**: Version control and manage extraction prompts systematically
> **MCP Validated**: 2026-01-25

## When to Use

- Production systems with evolving prompts
- A/B testing different prompt versions
- Audit trails for extraction logic
- Team collaboration on prompt engineering

## Implementation

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
import json
import hashlib


@dataclass
class PromptVersion:
    """A versioned prompt configuration."""
    version: str
    prompt_text: str
    schema: dict
    model: str = "gemini-2.5-flash"
    temperature: float = 0.3
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    description: str = ""
    active: bool = True

    @property
    def content_hash(self) -> str:
        content = f"{self.prompt_text}{json.dumps(self.schema, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]


class PromptRegistry:
    """Manage versioned prompts with persistence."""

    def __init__(self, registry_path: str = ".prompts/registry.json"):
        self.registry_path = Path(registry_path)
        self.prompts: Dict[str, Dict[str, PromptVersion]] = {}
        self._load()

    def _load(self):
        if self.registry_path.exists():
            data = json.loads(self.registry_path.read_text())
            for task_name, versions in data.items():
                self.prompts[task_name] = {v: PromptVersion(**c) for v, c in versions.items()}

    def _save(self):
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {t: {v: vars(p) for v, p in vers.items()} for t, vers in self.prompts.items()}
        self.registry_path.write_text(json.dumps(data, indent=2))

    def register(self, task_name: str, prompt_text: str, schema: dict,
                 version: Optional[str] = None, **kwargs) -> PromptVersion:
        if task_name not in self.prompts:
            self.prompts[task_name] = {}
        if version is None:
            version = f"v{len(self.prompts[task_name]) + 1}.0"
        prompt = PromptVersion(version=version, prompt_text=prompt_text, schema=schema, **kwargs)
        self.prompts[task_name][version] = prompt
        self._save()
        return prompt

    def get_active(self, task_name: str) -> Optional[PromptVersion]:
        versions = self.prompts.get(task_name, {})
        for prompt in sorted(versions.values(), key=lambda p: p.version, reverse=True):
            if prompt.active:
                return prompt
        return None

    def get_version(self, task_name: str, version: str) -> Optional[PromptVersion]:
        return self.prompts.get(task_name, {}).get(version)

    def list_versions(self, task_name: str) -> List[str]:
        return list(self.prompts.get(task_name, {}).keys())


# Pre-defined invoice prompts
INVOICE_V1 = PromptVersion(
    version="v1.0",
    description="Basic extraction",
    prompt_text="Extract invoice data: invoice_id, vendor_name, date, total.",
    schema={"type": "object", "properties": {
        "invoice_id": {"type": "string"}, "vendor_name": {"type": "string"},
        "invoice_date": {"type": "string"}, "total_amount": {"type": "number"}
    }, "required": ["invoice_id", "total_amount"]}
)

INVOICE_V2 = PromptVersion(
    version="v2.0",
    description="With line items",
    prompt_text="""Extract all invoice information.
- Convert dates to YYYY-MM-DD
- Include line items with descriptions, quantities, totals""",
    schema={"type": "object", "properties": {
        "invoice_id": {"type": "string"}, "vendor_name": {"type": "string"},
        "total_amount": {"type": "number"},
        "line_items": {"type": "array", "items": {"type": "object", "properties": {
            "description": {"type": "string"}, "quantity": {"type": "number"},
            "total": {"type": "number"}}}}
    }, "required": ["invoice_id", "total_amount"]}
)
```

## Configuration

| Setting | Description |
|---------|-------------|
| `registry_path` | JSON file for prompt persistence |
| `version` | Semantic version string (v1.0, v2.0) |
| `content_hash` | Auto-generated change detection hash |

## Example Usage

```python
registry = PromptRegistry(".prompts/registry.json")

# Register new prompt
registry.register(
    task_name="invoice_extraction",
    prompt_text="Extract invoice data...",
    schema={"type": "object", ...}
)

# Get active prompt
prompt = registry.get_active("invoice_extraction")
response = client.models.generate_content(
    model=prompt.model,
    contents=[content],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=prompt.schema
    )
)
```

## See Also

- [invoice-extraction.md](invoice-extraction.md)
- [structured-json-output.md](structured-json-output.md)
