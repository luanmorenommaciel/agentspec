# Slack Integration Pattern

> **Purpose**: Alert notifications and incident reporting via Slack webhooks
> **MCP Validated**: 2026-01-25

## When to Use

- Sending incident alerts to operations channels
- Formatting structured reports for human review
- Creating interactive approval workflows
- Tracking incident resolution status

## Implementation

```python
from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import requests
import os

# ============ SLACK ALERT TOOL ============
class SlackAlertInput(BaseModel):
    channel: str = Field(description="Slack channel (e.g., #dataops-alerts)")
    title: str = Field(description="Alert title/header")
    severity: str = Field(description="CRITICAL, ERROR, WARNING, INFO")
    message: str = Field(description="Alert body with details")
    fields: str = Field(default="", description="JSON string of key-value fields")

class SlackAlertTool(BaseTool):
    name: str = "Send Slack Alert"
    description: str = """Send formatted alert to Slack channel.
    Use for incident notifications and status updates."""
    args_schema: Type[BaseModel] = SlackAlertInput

    severity_colors = {
        "CRITICAL": "#FF0000",
        "ERROR": "#FFA500",
        "WARNING": "#FFFF00",
        "INFO": "#0000FF"
    }
    severity_emoji = {
        "CRITICAL": ":red_circle:",
        "ERROR": ":warning:",
        "WARNING": ":large_yellow_circle:",
        "INFO": ":information_source:"
    }

    def _run(self, channel: str, title: str, severity: str,
             message: str, fields: str = "") -> str:
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        if not webhook_url:
            return "Error: SLACK_WEBHOOK_URL not configured"

        import json
        color = self.severity_colors.get(severity.upper(), "#808080")
        emoji = self.severity_emoji.get(severity.upper(), ":bell:")

        # Build attachment
        attachment = {
            "color": color,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{emoji} {title}"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message}
                }
            ]
        }

        # Add fields if provided
        if fields:
            field_data = json.loads(fields)
            field_elements = []
            for key, value in field_data.items():
                field_elements.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{value}"
                })
            attachment["blocks"].append({
                "type": "section",
                "fields": field_elements[:10]  # Slack limit
            })

        payload = {
            "channel": channel,
            "attachments": [attachment]
        }

        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            return f"Alert sent to {channel}: {title}"
        return f"Failed to send alert: {response.text}"

# ============ REPORTER AGENT ============
reporter_agent = Agent(
    role="Incident Reporter",
    goal="Create clear, actionable incident reports for Slack",
    backstory="""You are a technical writer specializing in incident
    communication. You create reports that are concise, informative,
    and include clear next steps. You know how to format messages
    for maximum readability in Slack.""",
    tools=[SlackAlertTool()],
    llm="gemini/gemini-1.5-flash",
    max_iter=5,
    verbose=True
)

# ============ REPORTING TASK ============
incident_report_task = Task(
    description="""Create incident report from analysis and send to Slack.

    Analysis: {analysis_summary}

    Format the report with:
    1. Clear severity indicator
    2. Affected services
    3. Impact description
    4. Root cause (if known)
    5. Recommended actions
    6. ETA for resolution (if applicable)

    Send to channel: {slack_channel}""",
    expected_output="Confirmation that Slack alert was sent successfully",
    agent=reporter_agent
)
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `SLACK_WEBHOOK_URL` | env var | Incoming webhook URL |
| `max_iter` | 5 | Low - simple formatting task |
| `channel` | `#dataops-alerts` | Target channel |

## Message Formatting

| Element | Slack Markup | Example |
|---------|--------------|---------|
| Bold | `*text*` | `*CRITICAL*` |
| Code | `` `code` `` | `` `BigQuery` `` |
| Link | `<url\|text>` | `<http://...\|Dashboard>` |
| Emoji | `:name:` | `:red_circle:` |

## Example Usage

```python
from crewai import Crew, Process

# Standalone reporter crew
reporter_crew = Crew(
    agents=[reporter_agent],
    tasks=[incident_report_task],
    process=Process.sequential,
    verbose=True
)

result = reporter_crew.kickoff(inputs={
    "analysis_summary": """
    - 3 Cloud Run instances crashed due to OOM
    - Root cause: Batch size too large for memory limit
    - Fix: Reduce batch size or increase memory
    """,
    "slack_channel": "#dataops-alerts"
})
```

## Slack Webhook Setup

1. Go to Slack App Directory > Incoming Webhooks
2. Create new webhook for your workspace
3. Select target channel
4. Copy webhook URL to `SLACK_WEBHOOK_URL` env var
5. Store securely in Secret Manager for production

## See Also

- [Triage Pattern](../patterns/triage-investigation-report.md)
- [Escalation Workflow](../patterns/escalation-workflow.md)
- [Tools Concept](../concepts/tools.md)
