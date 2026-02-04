# Knowledge Base (KB) Framework

The KB framework grounds agent responses in your actual codebase patterns.

## Structure

```
kb/
├── _templates/           # Templates for new domains
│   ├── concept.md.template
│   ├── pattern.md.template
│   ├── index.md.template
│   └── quick-reference.md.template
│
└── {domain}/             # Your KB domains
    ├── index.md          # Domain overview
    ├── quick-reference.md # Cheat sheet
    ├── concepts/         # Core concepts
    │   ├── concept-1.md
    │   └── concept-2.md
    └── patterns/         # Implementation patterns
        ├── pattern-1.md
        └── pattern-2.md
```

## Creating a KB Domain

Use the `/create-kb` command:

```bash
claude> /create-kb redis "Caching layer patterns"
```

Or manually:

1. Copy `_templates/` structure
2. Fill in domain-specific content
3. Include code examples from your codebase

## Included Domains

### pydantic/

Data validation patterns for Python:

- Concepts: BaseModel, Field types, Validators, Nested models
- Patterns: LLM output validation, Error handling, Extraction schemas

## Best Practices

1. **Be specific** - Reference actual code from your project
2. **Include examples** - Working code snippets
3. **Keep updated** - Mark stale content
4. **Cite sources** - Link to official docs
