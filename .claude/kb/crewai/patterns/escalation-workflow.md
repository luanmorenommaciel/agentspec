# Escalation Workflow Pattern

> **Purpose**: Agent-to-human handoff for critical decisions and approvals
> **MCP Validated**: 2026-01-25

## When to Use

- Critical incidents requiring human judgment
- Actions with irreversible consequences (delete, scale down)
- Low confidence analysis needing human verification
- Compliance requirements mandating human approval

## Implementation

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
import os

# ============ ESCALATION TOOLS ============
@tool("Request Human Approval")
def request_human_approval(action: str, reason: str, urgency: str) -> str:
    """Request human approval for critical action via Slack.
    Use when action is irreversible or confidence is low.

    Args:
        action: What needs to be done
        reason: Why this action is recommended
        urgency: HIGH (< 15 min), MEDIUM (< 1 hour), LOW (< 4 hours)

    Returns:
        Approval status message
    """
    import requests
    webhook = os.environ.get("SLACK_ESCALATION_WEBHOOK")

    emoji = {"HIGH": ":red_circle:", "MEDIUM": ":large_orange_diamond:", "LOW": ":white_circle:"}
    payload = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji.get(urgency, '')} Approval Required"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Action:* {action}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Reason:* {reason}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Urgency:* {urgency}"}},
            {"type": "actions", "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "value": "approve", "action_id": "approve"},
                {"type": "button", "text": {"type": "plain_text", "text": "Deny"}, "value": "deny", "action_id": "deny"}
            ]}
        ]
    }
    requests.post(webhook, json=payload)
    return f"Escalation sent. Awaiting human approval for: {action}"

# ============ ESCALATION AGENT ============
escalation_agent = Agent(
    role="Escalation Coordinator",
    goal="Route critical issues to humans and track resolution",
    backstory="""You are the bridge between automated systems and human
    operators. You know when AI can handle an issue and when it needs
    human judgment. You never authorize irreversible actions without
    explicit human approval.""",
    tools=[request_human_approval],
    llm="gemini/gemini-1.5-flash",
    max_iter=5,
    allow_delegation=False,
    verbose=True
)

# ============ HIERARCHICAL CREW WITH ESCALATION ============
triage_agent = Agent(
    role="Triage Specialist",
    goal="Classify issues and route appropriately",
    backstory="Expert at prioritizing incidents by severity and impact.",
    allow_delegation=True,  # Can delegate to escalation
    llm="gemini/gemini-1.5-flash",
    max_iter=10
)

# Task with human input option
critical_task = Task(
    description="""Analyze the incident and determine action:

    If severity is CRITICAL and action is irreversible:
    - Use Request Human Approval tool
    - Wait for approval before proceeding

    If severity is ERROR but action is safe:
    - Proceed with automated remediation

    Incident: {incident_description}""",
    expected_output="""Decision report:
    - Severity: [CRITICAL/ERROR/WARNING]
    - Recommended Action: [description]
    - Escalated: [yes/no]
    - Human Approval: [pending/approved/not required]""",
    agent=triage_agent,
    human_input=False  # Use tool-based escalation instead
)

# Alternative: Direct human input on task
human_review_task = Task(
    description="Review the analysis and approve remediation plan",
    expected_output="Human decision: approved/denied with comments",
    agent=escalation_agent,
    human_input=True  # Blocks for human input
)
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `human_input` | True/False | Block task for human input |
| `allow_delegation` | True | Enable agent-to-agent handoff |
| `max_iter` | 5 | Low for escalation (simple routing) |

## Escalation Matrix

| Severity | Confidence | Action |
|----------|------------|--------|
| CRITICAL | Any | Always escalate |
| ERROR | < 80% | Escalate for review |
| ERROR | >= 80% | Auto-remediate, notify |
| WARNING | Any | Log and monitor |

## Example Usage

```python
# Crew with escalation path
escalation_crew = Crew(
    agents=[triage_agent, escalation_agent],
    tasks=[critical_task],
    process=Process.hierarchical,  # Manager can route to escalation
    manager_llm="gemini/gemini-1.5-pro",
    verbose=True
)

result = escalation_crew.kickoff(inputs={
    "incident_description": "BigQuery slot exhaustion - queries failing"
})
```

## Best Practices

| Do | Don't |
|----|-------|
| Escalate irreversible actions | Auto-delete without approval |
| Set clear urgency levels | Mark everything HIGH |
| Include context in escalation | Send vague alerts |
| Track escalation resolution | Fire and forget |

## See Also

- [Triage Pattern](../patterns/triage-investigation-report.md)
- [Circuit Breaker](../patterns/circuit-breaker.md)
- [Processes Concept](../concepts/processes.md)
