# Create Knowledge Base Command

> Create a complete KB section from scratch with MCP validation.

## Usage

```
/create-kb <DOMAIN>
```

**Examples**: `/create-kb redis`, `/create-kb pandas`, `/create-kb authentication`

## What Happens

1. **Validates prerequisites** — checks `_templates/` and `_index.yaml` exist
2. **Invokes kb-architect agent** — executes full workflow
3. **Reports completion** — shows score and files created

## Options

| Command | Action |
|---------|--------|
| `/create-kb <domain>` | Create new KB domain |
| `/create-kb --audit` | Audit existing KB health |

## See Also

- **Agent**: `.claude/agents/exploration/kb-architect.md`
- **Example**: `.claude/kb/llmops/`
- **Templates**: `.claude/kb/_templates/`
- **Registry**: `.claude/kb/_index.yaml`
