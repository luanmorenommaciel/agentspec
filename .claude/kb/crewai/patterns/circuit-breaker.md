# Circuit Breaker Pattern

> **Purpose**: Preventing runaway agents with iteration limits and safeguards
> **MCP Validated**: 2026-01-25

## When to Use

- Preventing infinite loops in agent reasoning
- Controlling LLM API costs during development
- Setting execution time boundaries
- Handling agent failures gracefully

## Implementation

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
import time

# ============ CIRCUIT BREAKER CONFIGURATION ============
CIRCUIT_BREAKER_CONFIG = {
    "max_iterations": 15,      # Max reasoning loops
    "max_execution_time": 300,  # 5 minutes max
    "max_retry_limit": 2,       # Retries on error
    "respect_context_window": True,  # Fail on context overflow
    "max_rpm": 30               # Rate limit API calls
}

# ============ SAFE AGENT WITH LIMITS ============
safe_agent = Agent(
    role="Bounded Analyst",
    goal="Analyze logs within strict resource limits",
    backstory="You work efficiently within constraints.",
    llm="gemini/gemini-1.5-flash",
    max_iter=CIRCUIT_BREAKER_CONFIG["max_iterations"],
    max_retry_limit=CIRCUIT_BREAKER_CONFIG["max_retry_limit"],
    max_execution_time=CIRCUIT_BREAKER_CONFIG["max_execution_time"],
    respect_context_window=CIRCUIT_BREAKER_CONFIG["respect_context_window"],
    verbose=True
)

# ============ EXECUTION WRAPPER ============
class CircuitBreaker:
    """Wrap crew execution with circuit breaker logic."""

    def __init__(self, crew: Crew, config: dict):
        self.crew = crew
        self.config = config
        self.failure_count = 0
        self.max_failures = 3
        self.is_open = False

    def execute(self, inputs: dict) -> dict:
        """Execute crew with circuit breaker protection."""
        if self.is_open:
            return {
                "status": "circuit_open",
                "message": "Circuit breaker is open. Manual reset required.",
                "failure_count": self.failure_count
            }

        start_time = time.time()
        try:
            result = self.crew.kickoff(inputs=inputs)
            self.failure_count = 0  # Reset on success
            return {
                "status": "success",
                "result": result,
                "execution_time": time.time() - start_time
            }

        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.max_failures:
                self.is_open = True

            return {
                "status": "failure",
                "error": str(e),
                "failure_count": self.failure_count,
                "circuit_open": self.is_open
            }

    def reset(self):
        """Manual reset of circuit breaker."""
        self.failure_count = 0
        self.is_open = False

# ============ CREW WITH RATE LIMITING ============
bounded_crew = Crew(
    agents=[safe_agent],
    tasks=[Task(
        description="Analyze {log_path} for errors",
        expected_output="Error summary",
        agent=safe_agent
    )],
    process=Process.sequential,
    max_rpm=CIRCUIT_BREAKER_CONFIG["max_rpm"],
    verbose=True
)

# ============ USAGE ============
breaker = CircuitBreaker(bounded_crew, CIRCUIT_BREAKER_CONFIG)
result = breaker.execute({"log_path": "/tmp/logs/app.log"})

if result["status"] == "circuit_open":
    # Alert humans - system needs attention
    print(f"ALERT: Circuit breaker opened after {result['failure_count']} failures")
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_iter` | 20 | Max reasoning iterations per agent |
| `max_execution_time` | None | Timeout in seconds |
| `max_retry_limit` | 2 | Retries on error |
| `max_rpm` | None | Crew-level rate limit |
| `respect_context_window` | True | Fail on context overflow |

## Agent-Level Limits

```python
# Conservative limits for triage (fast, focused)
triage_agent = Agent(
    role="Triage",
    max_iter=10,          # Quick decisions
    max_retry_limit=1,    # Fail fast
    max_execution_time=60  # 1 minute max
)

# Higher limits for deep analysis
analyst_agent = Agent(
    role="Analyst",
    max_iter=20,          # More reasoning allowed
    max_retry_limit=3,    # More retries
    max_execution_time=300 # 5 minutes max
)
```

## Error Handling

| Error | Response | Recovery |
|-------|----------|----------|
| Max iterations | Stop, return partial | Reduce scope, retry |
| Timeout | Kill execution | Alert, escalate |
| Context overflow | Fail with error | Chunk input |
| API rate limit | Backoff, retry | Lower max_rpm |

## Best Practices

| Do | Don't |
|----|-------|
| Set max_iter based on task complexity | Use default 20 for all |
| Monitor execution times | Ignore slow runs |
| Log circuit breaker events | Fail silently |
| Alert on repeated failures | Auto-reset blindly |

## See Also

- [Agents Concept](../concepts/agents.md)
- [Escalation Workflow](../patterns/escalation-workflow.md)
- [Crew Coordination](../patterns/crew-coordination.md)
