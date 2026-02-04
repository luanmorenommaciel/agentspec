# Log Analysis Agent Pattern

> **Purpose**: Custom tools for reading and parsing GCS log exports
> **MCP Validated**: 2026-01-25

## When to Use

- Analyzing Cloud Logging exports stored in GCS
- Parsing structured JSON logs from Cloud Run, Pub/Sub, BigQuery
- Filtering high-volume logs to find relevant events
- Building agents that need access to infrastructure logs

## Implementation

```python
from crewai import Agent, Task
from crewai.tools import tool, BaseTool
from pydantic import BaseModel, Field
from typing import Type, List
from google.cloud import storage
import json

# ============ GCS LOG READER TOOL ============
@tool("Read GCS Logs")
def read_gcs_logs(bucket: str, prefix: str, max_files: int = 10) -> str:
    """Read log files from GCS bucket with given prefix.
    Use for analyzing Cloud Logging exports.

    Args:
        bucket: GCS bucket name (e.g., 'project-logs-export')
        prefix: Path prefix (e.g., 'cloud-run/2026/01/25/')
        max_files: Maximum files to read (default: 10)

    Returns:
        Combined log content as JSON array
    """
    client = storage.Client()
    bucket_obj = client.bucket(bucket)
    blobs = list(bucket_obj.list_blobs(prefix=prefix, max_results=max_files))

    all_logs = []
    for blob in blobs:
        content = blob.download_as_text()
        # Handle newline-delimited JSON
        for line in content.strip().split('\n'):
            if line:
                all_logs.append(json.loads(line))

    return json.dumps(all_logs, indent=2)

# ============ LOG FILTER TOOL ============
class LogFilterInput(BaseModel):
    logs_json: str = Field(description="JSON string of log entries")
    severity: str = Field(description="Minimum severity: INFO, WARNING, ERROR, CRITICAL")
    service: str = Field(default="", description="Filter by service name (optional)")

class LogFilterTool(BaseTool):
    name: str = "Filter Logs"
    description: str = """Filter log entries by severity and service.
    Use after reading logs to focus on relevant entries."""
    args_schema: Type[BaseModel] = LogFilterInput

    severity_order = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 3}

    def _run(self, logs_json: str, severity: str, service: str = "") -> str:
        logs = json.loads(logs_json)
        min_level = self.severity_order.get(severity.upper(), 0)

        filtered = []
        for log in logs:
            log_severity = log.get("severity", "INFO")
            log_level = self.severity_order.get(log_severity, 0)

            if log_level >= min_level:
                if not service or service.lower() in log.get("resource", {}).get("type", "").lower():
                    filtered.append(log)

        return json.dumps(filtered, indent=2)

# ============ LOG ANALYSIS AGENT ============
log_analysis_agent = Agent(
    role="Log Analysis Engineer",
    goal="Extract actionable insights from infrastructure logs",
    backstory="""You are an expert at analyzing GCP logs. You've seen
    every type of Cloud Run crash, Pub/Sub backlog, and BigQuery timeout.
    You quickly identify patterns and separate signal from noise.""",
    tools=[read_gcs_logs, LogFilterTool()],
    llm="gemini/gemini-1.5-pro",
    max_iter=15,
    verbose=True
)

# ============ ANALYSIS TASK ============
log_analysis_task = Task(
    description="""Analyze logs from GCS bucket '{bucket}' with prefix '{prefix}'.

    Steps:
    1. Read logs using Read GCS Logs tool
    2. Filter to ERROR and CRITICAL using Filter Logs tool
    3. Identify patterns (recurring errors, spike times, affected services)
    4. Summarize findings with counts and examples

    Focus on: Cloud Run failures, Pub/Sub delivery issues, BigQuery errors""",
    expected_output="""Analysis report:
    ## Summary
    - Total events analyzed: N
    - Errors found: N
    - Critical issues: N

    ## Patterns Identified
    1. [Pattern description with count]
    2. [Pattern description with count]

    ## Sample Errors
    [Top 3 error messages with timestamps]

    ## Recommendations
    [Actionable next steps]""",
    agent=log_analysis_agent
)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_files` | 10 | Limit files per read to control costs |
| `max_iter` | 15 | Allow thorough analysis |
| `severity` | ERROR | Minimum severity to process |

## Example Usage

```python
from crewai import Crew, Process

# Create crew with just the analysis agent
analysis_crew = Crew(
    agents=[log_analysis_agent],
    tasks=[log_analysis_task],
    process=Process.sequential,
    verbose=True
)

# Run analysis
result = analysis_crew.kickoff(inputs={
    "bucket": "invoice-pipeline-logs",
    "prefix": "cloud-run/2026/01/25/"
})

print(result)
```

## GCP Log Structure

| Field | Description | Example |
|-------|-------------|---------|
| `severity` | Log level | `ERROR` |
| `timestamp` | ISO timestamp | `2026-01-25T10:30:00Z` |
| `resource.type` | GCP service | `cloud_run_revision` |
| `textPayload` | Log message | `Connection timeout` |
| `jsonPayload` | Structured data | `{"error": "..."}` |

## See Also

- [Tools Concept](../concepts/tools.md)
- [Triage Pattern](../patterns/triage-investigation-report.md)
- [Circuit Breaker](../patterns/circuit-breaker.md)
