# Triage-Investigation-Report Pattern

> **Purpose**: Three-agent architecture for autonomous DataOps monitoring
> **MCP Validated**: 2026-01-25

## When to Use

- Pipeline monitoring with automated severity classification
- Log analysis requiring root cause investigation
- Alert systems with formatted reports to Slack
- Self-healing infrastructure with autonomous remediation

## Implementation

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
import os

# ============ CUSTOM TOOLS ============
@tool("Read Log File")
def read_log_file(file_path: str) -> str:
    """Read log file from local path or GCS.
    Use for analyzing Cloud Run, Pub/Sub, or BigQuery logs."""
    # Simplified - add GCS client for production
    with open(file_path) as f:
        return f.read()

@tool("Send Slack Alert")
def send_slack_alert(channel: str, message: str) -> str:
    """Send alert to Slack channel via webhook.
    Use after analysis is complete to notify the team."""
    import requests
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    requests.post(webhook, json={"channel": channel, "text": message})
    return f"Alert sent to {channel}"

# ============ AGENTS ============
triage_agent = Agent(
    role="Log Triage Specialist",
    goal="Classify log events by severity and filter noise",
    backstory="""Expert DevOps engineer with deep knowledge of GCP
    services. You quickly identify CRITICAL and ERROR events while
    filtering out routine INFO messages.""",
    tools=[read_log_file],
    llm="gemini/gemini-1.5-flash",
    max_iter=10,
    verbose=True
)

root_cause_agent = Agent(
    role="Root Cause Analyst",
    goal="Identify root cause of errors and suggest fixes",
    backstory="""Senior SRE specializing in data pipelines. You've
    debugged hundreds of Cloud Run, Pub/Sub, and BigQuery issues.
    You find patterns and provide actionable recommendations.""",
    tools=[read_log_file],
    llm="gemini/gemini-1.5-pro",
    max_iter=15,
    verbose=True
)

reporter_agent = Agent(
    role="Alert Reporter",
    goal="Format clear incident reports and notify stakeholders",
    backstory="""Technical writer who excels at summarizing complex
    issues. You create actionable alerts with severity, impact,
    and recommended next steps.""",
    tools=[send_slack_alert],
    llm="gemini/gemini-1.5-flash",
    max_iter=5,
    verbose=True
)

# ============ TASKS ============
triage_task = Task(
    description="""Analyze logs at {log_path}. Classify each event:
    - CRITICAL: Service down, data loss risk
    - ERROR: Failed operations, retryable
    - WARNING: Degraded performance
    - INFO: Routine operations (filter these out)

    Output only CRITICAL and ERROR events.""",
    expected_output="""JSON array: [{"severity": "...", "service": "...",
    "timestamp": "...", "message": "...", "count": N}]""",
    agent=triage_agent
)

analysis_task = Task(
    description="""Analyze the classified errors from triage.
    For each error pattern:
    1. Identify likely root cause
    2. Check if transient or persistent
    3. Suggest remediation steps""",
    expected_output="""Root cause report:
    - Error: [description]
    - Root Cause: [analysis]
    - Remediation: [steps]
    - Auto-fix possible: [yes/no]""",
    agent=root_cause_agent,
    context=[triage_task]
)

report_task = Task(
    description="""Create incident report and send to Slack #{slack_channel}.
    Include severity summary, affected services, and action items.""",
    expected_output="Confirmation of Slack notification sent",
    agent=reporter_agent,
    context=[triage_task, analysis_task]
)

# ============ CREW ============
monitoring_crew = Crew(
    agents=[triage_agent, root_cause_agent, reporter_agent],
    tasks=[triage_task, analysis_task, report_task],
    process=Process.sequential,
    memory=True,
    verbose=True
)

# ============ EXECUTION ============
result = monitoring_crew.kickoff(inputs={
    "log_path": "/tmp/logs/cloud-run-2026-01-25.json",
    "slack_channel": "dataops-alerts"
})
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `triage_agent.max_iter` | 10 | Limit iterations for fast triage |
| `root_cause_agent.max_iter` | 15 | More iterations for deep analysis |
| `reporter_agent.max_iter` | 5 | Minimal for simple reporting |
| `crew.memory` | True | Learn from past incidents |

## Example Usage

```python
# Triggered by Cloud Scheduler or Pub/Sub
def handle_log_event(event, context):
    log_path = event["bucket"] + "/" + event["name"]
    result = monitoring_crew.kickoff(inputs={
        "log_path": log_path,
        "slack_channel": "dataops-alerts"
    })
    return result
```

## See Also

- [Log Analysis Agent](../patterns/log-analysis-agent.md)
- [Slack Integration](../patterns/slack-integration.md)
- [Agents Concept](../concepts/agents.md)
