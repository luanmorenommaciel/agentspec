# Tasks

> **Purpose**: Units of work with clear descriptions and expected outputs
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Tasks define specific work units for agents to complete. Each task includes a description of what needs to be done and an expected output format. Tasks can depend on other tasks through context, enabling data flow between agents in a crew.

## The Pattern

```python
from crewai import Task

# Log Triage Task
triage_task = Task(
    description="""Analyze the log file at {log_path} and classify
    each event by severity: CRITICAL, ERROR, WARNING, INFO.

    Focus on:
    - Cloud Run failures
    - Pub/Sub delivery issues
    - BigQuery errors
    - LLM API timeouts

    Filter out routine INFO messages.""",
    expected_output="""JSON array of classified events:
    [{"timestamp": "...", "severity": "ERROR",
      "service": "cloud-run", "message": "..."}]""",
    agent=triage_agent,
    async_execution=False
)

# Analysis Task (depends on triage)
analysis_task = Task(
    description="Analyze the classified errors and find root cause",
    expected_output="Root cause analysis with suggested fix",
    agent=root_cause_agent,
    context=[triage_task]  # Receives triage output
)
```

## Quick Reference

| Parameter | Required | Description |
|-----------|----------|-------------|
| `description` | Yes | What the agent should do |
| `expected_output` | Yes | Format/structure of result |
| `agent` | Yes | Agent assigned to this task |
| `context` | No | List of dependent tasks |
| `human_input` | No | Require human approval |
| `async_execution` | No | Run asynchronously |
| `output_json` | No | Pydantic model for JSON output |
| `output_file` | No | Save output to file path |

## Common Mistakes

### Wrong

```python
# Vague description, no expected output format
task = Task(
    description="Look at the logs",
    expected_output="Analysis",
    agent=agent
)
```

### Correct

```python
# Specific instructions, clear output format
task = Task(
    description="""Read Cloud Run logs from {log_path}.
    For each ERROR or CRITICAL entry:
    1. Extract timestamp, service name, error message
    2. Identify if it's a transient or persistent issue
    3. Check for recent similar errors (last 24h)""",
    expected_output="""Structured report with:
    - List of errors with timestamps
    - Severity classification
    - Pattern analysis (recurring vs one-time)
    - Recommended action (retry, investigate, escalate)""",
    agent=root_cause_agent,
    context=[triage_task]
)
```

## Task Output Options

| Option | Use Case |
|--------|----------|
| `output_json=Model` | Validate with Pydantic |
| `output_file="report.md"` | Save to disk |
| `callback=fn` | Post-processing function |

## Related

- [Agents](../concepts/agents.md)
- [Tools](../concepts/tools.md)
- [Escalation Workflow](../patterns/escalation-workflow.md)
