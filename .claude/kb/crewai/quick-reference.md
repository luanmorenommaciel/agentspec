# CrewAI Quick Reference

> Fast lookup tables. For code examples, see linked files.
> **MCP Validated**: 2026-01-25

## Agent Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `role` | str | required | Agent's job title/function |
| `goal` | str | required | What the agent aims to achieve |
| `backstory` | str | required | Context shaping agent behavior |
| `tools` | list | `[]` | Tools available to the agent |
| `llm` | LLM | GPT-4 | Language model to use |
| `allow_delegation` | bool | `False` | Can delegate to other agents |
| `max_iter` | int | `20` | Maximum reasoning iterations |
| `max_retry_limit` | int | `2` | Retries on error |

## Task Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `description` | str | required | What needs to be done |
| `expected_output` | str | required | Format/content of result |
| `agent` | Agent | required | Who performs the task |
| `context` | list | `[]` | Dependent tasks for context |
| `human_input` | bool | `False` | Require human approval |
| `async_execution` | bool | `False` | Run asynchronously |

## Process Types

| Process | Use Case | Manager |
|---------|----------|---------|
| `sequential` | Linear workflows, predictable | No |
| `hierarchical` | Complex projects, dynamic | Yes (auto/manual) |

## Memory Types

| Memory | Storage | Purpose |
|--------|---------|---------|
| Short-term | ChromaDB (RAG) | Current context within execution |
| Long-term | SQLite3 | Learning across sessions |
| Entity | ChromaDB (RAG) | People, places, concepts tracking |

## Severity Classification (DataOps)

| Level | Action | SLA |
|-------|--------|-----|
| CRITICAL | Immediate escalation | < 5 min |
| ERROR | Root cause analysis | < 15 min |
| WARNING | Log and monitor | < 1 hour |
| INFO | Archive only | N/A |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Use `allow_delegation=True` on all agents | Enable only when needed |
| Skip `expected_output` | Always define output format |
| Ignore `max_iter` limits | Set appropriate bounds |
| Use hierarchical for simple tasks | Use sequential for linear flows |

## Related Documentation

| Topic | Path |
|-------|------|
| Agent Concepts | `concepts/agents.md` |
| Custom Tools | `concepts/tools.md` |
| Three-Agent Pattern | `patterns/triage-investigation-report.md` |
| Full Index | `index.md` |
