# Processes

> **Purpose**: Execution flow control for agent collaboration
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Processes define how tasks are assigned and executed within a crew. CrewAI supports two process types: sequential (linear, predictable) and hierarchical (dynamic, manager-coordinated). The choice depends on workflow complexity and need for adaptive task allocation.

## The Pattern

```python
from crewai import Crew, Process

# Sequential: Tasks run in order
sequential_crew = Crew(
    agents=[triage_agent, root_cause_agent, reporter_agent],
    tasks=[triage_task, analysis_task, report_task],
    process=Process.sequential,  # Default
    verbose=True
)

# Hierarchical: Manager delegates dynamically
hierarchical_crew = Crew(
    agents=[triage_agent, root_cause_agent, reporter_agent],
    tasks=[complex_task],
    process=Process.hierarchical,
    manager_llm="gemini/gemini-1.5-pro",  # Or manager_agent
    verbose=True
)
```

## Quick Reference

| Process | Execution | Manager | Best For |
|---------|-----------|---------|----------|
| `sequential` | Fixed order | No | Linear workflows |
| `hierarchical` | Dynamic | Yes | Complex, adaptive |

## Sequential Process

Tasks execute in the order defined, output flows to next task via context.

```
Triage Task -> Analysis Task -> Report Task
     |              |              |
  triage_agent  root_cause_agent  reporter_agent
```

| Pros | Cons |
|------|------|
| Predictable | Inflexible |
| Easy to debug | No dynamic routing |
| Lower cost | Fixed path |

## Hierarchical Process

Manager agent assigns tasks based on agent capabilities.

```
        [Manager Agent]
       /       |       \
  triage   root_cause  reporter
  agent      agent      agent
```

| Pros | Cons |
|------|------|
| Adaptive | More LLM calls |
| Dynamic delegation | Harder to debug |
| Handles complexity | Higher cost |

## Common Mistakes

### Wrong

```python
# Using hierarchical for simple linear flow
crew = Crew(
    agents=[agent_a, agent_b],
    tasks=[task_1, task_2],  # Simple A->B flow
    process=Process.hierarchical  # Overkill
)
# Wastes tokens on manager overhead
```

### Correct

```python
# Match process to complexity
# Simple flow: sequential
simple_crew = Crew(
    agents=[triage, reporter],
    tasks=[triage_task, report_task],
    process=Process.sequential
)

# Complex with branching: hierarchical
complex_crew = Crew(
    agents=[triage, root_cause, reporter, escalation],
    tasks=[incident_response_task],
    process=Process.hierarchical,
    manager_llm="gemini/gemini-1.5-pro"
)
```

## DataOps Recommendation

| Scenario | Process | Reason |
|----------|---------|--------|
| Standard monitoring | Sequential | Predictable: Triage->Analyze->Report |
| Incident response | Hierarchical | May need escalation branching |
| High volume logs | Sequential | Lower cost per execution |

## Related

- [Crews](../concepts/crews.md)
- [Triage Pattern](../patterns/triage-investigation-report.md)
- [Escalation Workflow](../patterns/escalation-workflow.md)
