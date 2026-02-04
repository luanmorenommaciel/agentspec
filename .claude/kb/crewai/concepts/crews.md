# Crews

> **Purpose**: Team composition and orchestration of multiple agents
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

A Crew is a team of agents working together to accomplish related tasks. Crews define the collaboration strategy, task flow, and optional features like memory and planning. The crew orchestrates which agents work on which tasks and how they communicate.

## The Pattern

```python
from crewai import Crew, Process

# DataOps Monitoring Crew
monitoring_crew = Crew(
    agents=[triage_agent, root_cause_agent, reporter_agent],
    tasks=[triage_task, analysis_task, report_task],
    process=Process.sequential,
    memory=True,
    verbose=True,
    max_rpm=30,  # Rate limit API calls
    share_crew=False
)

# Execute the crew
result = monitoring_crew.kickoff()
```

## Quick Reference

| Parameter | Required | Description |
|-----------|----------|-------------|
| `agents` | Yes | List of Agent instances |
| `tasks` | Yes | List of Task instances |
| `process` | No | sequential or hierarchical |
| `memory` | No | Enable memory system (default: False) |
| `verbose` | No | Show execution details |
| `max_rpm` | No | Max requests per minute |
| `manager_llm` | No | LLM for hierarchical manager |

## Process Types

| Process | Best For | Characteristics |
|---------|----------|-----------------|
| `sequential` | Linear workflows | Predictable, easy to debug |
| `hierarchical` | Complex projects | Dynamic delegation, manager agent |

## Common Mistakes

### Wrong

```python
# Missing task dependencies - agents work in isolation
crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[task1, task2, task3],
    process=Process.sequential
)
# Tasks don't share context
```

### Correct

```python
# Tasks reference each other for context flow
triage_task = Task(description="...", agent=triage_agent)
analysis_task = Task(
    description="...",
    agent=root_cause_agent,
    context=[triage_task]  # Gets triage output
)
report_task = Task(
    description="...",
    agent=reporter_agent,
    context=[triage_task, analysis_task]  # Gets both outputs
)

crew = Crew(
    agents=[triage_agent, root_cause_agent, reporter_agent],
    tasks=[triage_task, analysis_task, report_task],
    process=Process.sequential,
    memory=True  # Enable for cross-task learning
)
```

## Kickoff Methods

| Method | Description |
|--------|-------------|
| `kickoff()` | Run crew synchronously |
| `kickoff_async()` | Run crew asynchronously |
| `kickoff_for_each(inputs)` | Run for each input item |

## Related

- [Agents](../concepts/agents.md)
- [Processes](../concepts/processes.md)
- [Crew Coordination](../patterns/crew-coordination.md)
