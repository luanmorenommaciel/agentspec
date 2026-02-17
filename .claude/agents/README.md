# AgentSpec Core Agents

AgentSpec includes **15 core agents** organized by category, all following the **KB-First architecture** with confidence scoring.

## Core Principle: KB-First Resolution

Every agent follows this mandatory resolution order:

```text
1. KB CHECK (local, instant, zero tokens)
   └─ Read: .claude/kb/{domain}/ → Project-specific patterns

2. CONFIDENCE ASSIGNMENT
   └─ Calculate score based on evidence quality

3. MCP FALLBACK (only if KB insufficient)
   └─ Query external sources for validation
```

## Categories

### Workflow Agents (6)

Drive the SDD workflow phases:

| Agent | Purpose | Phase |
|-------|---------|-------|
| `brainstorm-agent` | Explore ideas through collaborative dialogue | 0 |
| `define-agent` | Capture requirements with clarity scoring | 1 |
| `design-agent` | Create technical architecture with file manifest | 2 |
| `build-agent` | Execute implementation with agent delegation | 3 |
| `ship-agent` | Archive with lessons learned | 4 |
| `iterate-agent` | Update documents with cascade awareness | All |

### Code Quality Agents (4)

Ensure code excellence:

| Agent | Purpose |
|-------|---------|
| `code-reviewer` | Review code for quality and security issues |
| `code-cleaner` | Clean code, remove redundant comments, apply DRY |
| `code-documenter` | Generate documentation, READMEs, API docs |
| `test-generator` | Generate pytest tests with fixtures |

### Communication Agents (3)

Bridge technical and business:

| Agent | Purpose |
|-------|---------|
| `adaptive-explainer` | Explain concepts at any audience level |
| `meeting-analyst` | Extract decisions and action items from meetings |
| `the-planner` | Strategic architecture and roadmap planning |

### Exploration Agents (2)

Navigate and understand codebases:

| Agent | Purpose |
|-------|---------|
| `codebase-explorer` | Analyze codebase structure with health scoring |
| `kb-architect` | Build and audit knowledge base domains |

## Creating Custom Agents

Use `_template.md` as the definitive template. Key sections:

1. **Frontmatter** - name, description with examples, tools, kb_domains
2. **Identity Block** - Identity, Domain, Threshold
3. **Knowledge Architecture** - KB-First resolution order (mandatory)
4. **Capabilities** - What the agent can do
5. **Quality Gate** - Pre-flight checklist
6. **Response Format** - Consistent output with confidence scores
7. **Remember** - Mission and core principle

## Domain-Specific Examples

Additional domain-specific agents are available in `examples/agents/`:

| Category | Count | Examples |
|----------|-------|----------|
| `ai-ml/` | 4 | llm-specialist, genai-architect |
| `aws/` | 4 | lambda-builder, aws-deployer |
| `data-engineering/` | 8 | spark-specialist, lakeflow-expert |
| `developer/` | 1 | python-developer |

These serve as examples for creating your own domain-specific agents.
