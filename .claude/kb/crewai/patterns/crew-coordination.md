# Crew Coordination Pattern

> **Purpose**: Orchestrating multiple crews for pipeline monitoring
> **MCP Validated**: 2026-01-25

## When to Use

- Monitoring multiple pipeline stages independently
- Parallel analysis of different log sources
- Coordinating crews with different specializations
- Building modular, reusable monitoring components

## Implementation

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
import json

# ============ SPECIALIZED CREWS ============

# --- Cloud Run Monitoring Crew ---
cloud_run_agent = Agent(
    role="Cloud Run Specialist",
    goal="Monitor Cloud Run service health and performance",
    backstory="Expert in Cloud Run deployments, scaling, and errors.",
    llm="gemini/gemini-1.5-flash",
    max_iter=10
)

cloud_run_task = Task(
    description="Analyze Cloud Run logs at {log_path}. Check for OOM, cold starts, and timeouts.",
    expected_output="Cloud Run health report with issues and metrics",
    agent=cloud_run_agent
)

cloud_run_crew = Crew(
    agents=[cloud_run_agent],
    tasks=[cloud_run_task],
    process=Process.sequential,
    verbose=False
)

# --- Pub/Sub Monitoring Crew ---
pubsub_agent = Agent(
    role="Pub/Sub Specialist",
    goal="Monitor message delivery and subscription health",
    backstory="Expert in Pub/Sub patterns, dead letters, and backlog management.",
    llm="gemini/gemini-1.5-flash",
    max_iter=10
)

pubsub_task = Task(
    description="Analyze Pub/Sub logs at {log_path}. Check for delivery failures and backlog.",
    expected_output="Pub/Sub health report with delivery metrics",
    agent=pubsub_agent
)

pubsub_crew = Crew(
    agents=[pubsub_agent],
    tasks=[pubsub_task],
    process=Process.sequential,
    verbose=False
)

# --- BigQuery Monitoring Crew ---
bigquery_agent = Agent(
    role="BigQuery Specialist",
    goal="Monitor query performance and slot utilization",
    backstory="Expert in BigQuery optimization, costs, and troubleshooting.",
    llm="gemini/gemini-1.5-flash",
    max_iter=10
)

bigquery_task = Task(
    description="Analyze BigQuery logs at {log_path}. Check for slow queries and errors.",
    expected_output="BigQuery health report with performance metrics",
    agent=bigquery_agent
)

bigquery_crew = Crew(
    agents=[bigquery_agent],
    tasks=[bigquery_task],
    process=Process.sequential,
    verbose=False
)

# ============ CREW COORDINATOR ============
class CrewCoordinator:
    """Orchestrate multiple specialized crews."""

    def __init__(self):
        self.crews = {
            "cloud_run": cloud_run_crew,
            "pubsub": pubsub_crew,
            "bigquery": bigquery_crew
        }
        self.results = {}

    def run_parallel(self, inputs: Dict[str, dict]) -> Dict[str, any]:
        """Run multiple crews in parallel.

        Args:
            inputs: Dict mapping crew name to its inputs
                   e.g., {"cloud_run": {"log_path": "..."}, ...}
        """
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for crew_name, crew_inputs in inputs.items():
                if crew_name in self.crews:
                    future = executor.submit(
                        self.crews[crew_name].kickoff,
                        inputs=crew_inputs
                    )
                    futures[future] = crew_name

            for future in as_completed(futures):
                crew_name = futures[future]
                try:
                    self.results[crew_name] = {
                        "status": "success",
                        "result": future.result()
                    }
                except Exception as e:
                    self.results[crew_name] = {
                        "status": "error",
                        "error": str(e)
                    }

        return self.results

    def run_sequential(self, inputs: Dict[str, dict]) -> Dict[str, any]:
        """Run crews sequentially with dependency handling."""
        for crew_name, crew_inputs in inputs.items():
            if crew_name in self.crews:
                try:
                    result = self.crews[crew_name].kickoff(inputs=crew_inputs)
                    self.results[crew_name] = {"status": "success", "result": result}
                except Exception as e:
                    self.results[crew_name] = {"status": "error", "error": str(e)}
                    break  # Stop on first failure

        return self.results

# ============ USAGE ============
coordinator = CrewCoordinator()

# Run all monitoring crews in parallel
results = coordinator.run_parallel({
    "cloud_run": {"log_path": "/tmp/logs/cloud-run.json"},
    "pubsub": {"log_path": "/tmp/logs/pubsub.json"},
    "bigquery": {"log_path": "/tmp/logs/bigquery.json"}
})

# Aggregate results
for crew_name, result in results.items():
    print(f"{crew_name}: {result['status']}")
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `max_workers` | 3 | Parallel crew limit |
| `verbose` | False | Reduce noise in parallel runs |
| `max_iter` | 10 | Per-agent iteration limit |

## Coordination Patterns

| Pattern | Use Case | Implementation |
|---------|----------|----------------|
| Parallel | Independent analysis | ThreadPoolExecutor |
| Sequential | Dependent stages | Run in order |
| Fan-out/Fan-in | Aggregate results | Parallel + merge |

## Example: Aggregated Report

```python
# After parallel execution, aggregate into single report
aggregation_agent = Agent(
    role="Report Aggregator",
    goal="Combine crew results into unified report",
    backstory="Expert at synthesizing multiple data sources."
)

aggregation_task = Task(
    description="Combine these reports into unified status: {crew_results}",
    expected_output="Single pipeline health report",
    agent=aggregation_agent
)
```

## See Also

- [Crews Concept](../concepts/crews.md)
- [Triage Pattern](../patterns/triage-investigation-report.md)
- [Circuit Breaker](../patterns/circuit-breaker.md)
