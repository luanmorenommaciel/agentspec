# Agents

> **Purpose**: Autonomous AI units with roles, goals, backstories, and tools
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Agents are the fundamental building blocks of CrewAI. Each agent is a role-playing autonomous entity with a specific job function, goal, and backstory that shapes its decision-making. Agents can use tools, collaborate with other agents, and work toward completing assigned tasks.

## The Pattern

```python
from crewai import Agent

# DataOps Triage Agent Example
triage_agent = Agent(
    role="Log Triage Specialist",
    goal="Classify and prioritize log events by severity",
    backstory="""You are an expert DevOps engineer with 10 years
    of experience monitoring cloud infrastructure. You excel at
    quickly identifying critical issues from log noise.""",
    tools=[log_reader_tool, gcs_tool],
    llm="gemini/gemini-1.5-flash",
    allow_delegation=False,
    max_iter=15,
    max_retry_limit=2,
    verbose=True
)
```

## Quick Reference

| Parameter | Required | Description |
|-----------|----------|-------------|
| `role` | Yes | Job title (e.g., "Log Triage Specialist") |
| `goal` | Yes | What agent aims to achieve |
| `backstory` | Yes | Context shaping behavior |
| `tools` | No | List of available tools |
| `llm` | No | LLM to use (default: GPT-4) |
| `allow_delegation` | No | Can delegate tasks (default: False) |
| `max_iter` | No | Max iterations (default: 20) |

## Common Mistakes

### Wrong

```python
# Too vague - agent won't know what to do
agent = Agent(
    role="Helper",
    goal="Help with stuff",
    backstory="You help."
)
```

### Correct

```python
# Specific role, clear goal, detailed backstory
agent = Agent(
    role="Root Cause Analyst",
    goal="Identify the root cause of pipeline failures and suggest fixes",
    backstory="""You are a senior SRE specializing in data pipelines.
    You've debugged hundreds of Cloud Run, Pub/Sub, and BigQuery issues.
    You approach problems methodically, checking logs, metrics, and
    recent deployments to find the underlying cause.""",
    tools=[log_reader_tool, metrics_tool],
    max_iter=10  # Prevent runaway analysis
)
```

## Agent Types for DataOps

| Agent | Role | Goal |
|-------|------|------|
| Triage | Log Triage Specialist | Classify severity, filter noise |
| Root Cause | Root Cause Analyst | Find patterns, suggest fixes |
| Reporter | Alert Reporter | Format reports, notify Slack |

## Related

- [Crews](../concepts/crews.md)
- [Tasks](../concepts/tasks.md)
- [Triage Pattern](../patterns/triage-investigation-report.md)
