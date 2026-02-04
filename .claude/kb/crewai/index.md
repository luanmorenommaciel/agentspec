# CrewAI Knowledge Base

> **Purpose**: Multi-agent AI orchestration for autonomous DataOps monitoring and self-healing pipelines
> **MCP Validated**: 2026-01-25

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/agents.md](concepts/agents.md) | Role-playing autonomous agents with goals and tools |
| [concepts/crews.md](concepts/crews.md) | Team composition and collaboration orchestration |
| [concepts/tasks.md](concepts/tasks.md) | Work units with descriptions and expected outputs |
| [concepts/tools.md](concepts/tools.md) | Custom tools for log reading, Slack, and APIs |
| [concepts/memory.md](concepts/memory.md) | Short-term, long-term, and entity memory systems |
| [concepts/processes.md](concepts/processes.md) | Sequential and hierarchical execution flows |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/triage-investigation-report.md](patterns/triage-investigation-report.md) | Three-agent architecture for log monitoring |
| [patterns/log-analysis-agent.md](patterns/log-analysis-agent.md) | Custom tools for GCS log reading and parsing |
| [patterns/escalation-workflow.md](patterns/escalation-workflow.md) | Agent-to-human handoff and delegation |
| [patterns/slack-integration.md](patterns/slack-integration.md) | Alert notifications via Slack webhooks |
| [patterns/circuit-breaker.md](patterns/circuit-breaker.md) | Preventing runaway agents with iteration limits |
| [patterns/crew-coordination.md](patterns/crew-coordination.md) | Pipeline monitoring with coordinated crews |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables for agents, tasks, and processes

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Agent** | Autonomous unit with role, backstory, goal, and tools |
| **Crew** | Team of agents working together on related tasks |
| **Task** | Unit of work with description and expected output |
| **Tool** | Capability given to agents (log reader, Slack sender) |
| **Memory** | Persistent context across executions (STM, LTM, Entity) |
| **Process** | Execution flow (sequential or hierarchical) |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/agents.md, concepts/tasks.md |
| **Intermediate** | concepts/crews.md, patterns/triage-investigation-report.md |
| **Advanced** | patterns/circuit-breaker.md, patterns/escalation-workflow.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| Triage Agent | patterns/triage-investigation-report.md | Log classification and severity filtering |
| Root Cause Agent | patterns/log-analysis-agent.md | Error pattern analysis and fix suggestions |
| Reporter Agent | patterns/slack-integration.md | Alert formatting and notification delivery |

---

## Project Context

This KB supports the GenAI Invoice Processing Pipeline's DataOps monitoring:

```
Cloud Logging -> GCS Export -> CrewAI Triage -> Root Cause -> Reporter -> Slack
```

The three-agent architecture enables autonomous monitoring and self-healing capabilities.
