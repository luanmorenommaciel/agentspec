# Memory

> **Purpose**: Persistent context across tasks and executions
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

CrewAI's memory system enables agents to remember, reason, and learn from past interactions. The system includes short-term memory (current execution), long-term memory (across sessions), and entity memory (tracking people, places, concepts). Memory helps agents build context and improve over time.

## The Pattern

```python
from crewai import Crew, Process

# Enable memory with defaults
crew = Crew(
    agents=[triage_agent, root_cause_agent, reporter_agent],
    tasks=[triage_task, analysis_task, report_task],
    process=Process.sequential,
    memory=True,  # Enables STM, LTM, Entity memory
    verbose=True
)

# Memory persists learning across kickoffs
result1 = crew.kickoff(inputs={"log_path": "logs/day1.json"})
result2 = crew.kickoff(inputs={"log_path": "logs/day2.json"})
# Day 2 benefits from Day 1 learnings
```

## Memory Types

| Type | Storage | Purpose | Scope |
|------|---------|---------|-------|
| Short-term (STM) | ChromaDB | Current context | Single execution |
| Long-term (LTM) | SQLite3 | Past experiences | Across sessions |
| Entity | ChromaDB | People, concepts | Relationship mapping |

## Quick Reference

| Memory | Enabled By | Use Case |
|--------|------------|----------|
| Short-term | `memory=True` | Share context between tasks |
| Long-term | `memory=True` | Learn from past errors |
| Entity | `memory=True` | Track recurring services/patterns |

## Common Mistakes

### Wrong

```python
# Memory disabled - agents forget everything between runs
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=False  # Default - no learning
)

# Each kickoff starts fresh
crew.kickoff()  # Learns nothing
crew.kickoff()  # Starts from zero again
```

### Correct

```python
# Memory enabled for continuous learning
crew = Crew(
    agents=[triage_agent, root_cause_agent],
    tasks=[triage_task, analysis_task],
    memory=True,  # Enable all memory types
    embedder={
        "provider": "google",
        "config": {"model": "models/embedding-001"}
    }
)

# Agent learns that "OOM" errors correlate with batch size
# Next time it sees OOM, recalls the pattern faster
```

## Custom Memory Configuration

```python
from crewai.memory import ShortTermMemory, LongTermMemory, EntityMemory

crew = Crew(
    agents=[...],
    tasks=[...],
    short_term_memory=ShortTermMemory(
        storage=ChromaDB(path="./memory/stm")
    ),
    long_term_memory=LongTermMemory(
        storage=SQLiteDB(path="./memory/ltm.db")
    ),
    entity_memory=EntityMemory(
        storage=ChromaDB(path="./memory/entities")
    )
)
```

## DataOps Use Case

| Memory Type | DataOps Application |
|-------------|---------------------|
| STM | Triage results passed to Root Cause agent |
| LTM | "BigQuery quota errors happen on Mondays" |
| Entity | Track service names, error patterns |

## Related

- [Crews](../concepts/crews.md)
- [Crew Coordination](../patterns/crew-coordination.md)
