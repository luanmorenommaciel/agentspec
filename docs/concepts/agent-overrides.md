# Agent Overrides — Local-First Resolution

AgentSpec ships with 58 specialized agents, but every team has its own conventions. Rather than forking the plugin to customize phase behavior, you can drop a local agent file into your repo and it will take precedence over the plugin version.

## The Resolution Rule

```text
.claude/agents/<category>/<name>.md   ← your override (wins)
        ↓ if absent
${CLAUDE_PLUGIN_ROOT}/agents/<category>/<name>.md   ← AgentSpec plugin (fallback)
```

This is enforced by **Claude Code's native plugin loader** — when an agent name appears in both the user's project and a plugin, the user's version is what gets invoked. AgentSpec relies on this default rather than implementing a parallel resolver.

## When to Override

| Situation | Override |
|---|---|
| Your team has a non-standard PR template that `build-agent` should follow | `.claude/agents/workflow/build-agent.md` |
| `define-agent` should require a freshness SLA your shop tracks (e.g., DPP score) | `.claude/agents/workflow/define-agent.md` |
| `dbt-specialist` should default to your snapshot conventions | `.claude/agents/data-engineering/dbt-specialist.md` |
| `schema-designer` should always emit Data Vault, not star schema | `.claude/agents/architect/schema-designer.md` |
| You need a brand-new agent for a custom pipeline pattern | `.claude/agents/custom/<your-agent>.md` (no override — purely additive) |

## How to Override

`init-workspace.sh` (the SessionStart hook) creates these directories on first run:

```text
.claude/agents/
├── README.md       ← override pattern docs (auto-generated)
├── workflow/       ← drop overrides here for SDD phase agents
└── custom/         ← drop new agents here that don't replace anything
```

To override an existing AgentSpec agent:

```bash
# 1. Find the plugin agent
ls $CLAUDE_PLUGIN_ROOT/agents/workflow/

# 2. Copy it into your project
cp $CLAUDE_PLUGIN_ROOT/agents/workflow/build-agent.md \
   .claude/agents/workflow/build-agent.md

# 3. Edit your local copy — keep the `name:` field identical
$EDITOR .claude/agents/workflow/build-agent.md
```

The `name:` field in frontmatter must match the plugin agent's name exactly. That's how Claude Code knows your version replaces the plugin one.

## How to Add a Custom Agent

For agents that don't replace anything in AgentSpec — drop them in `custom/`:

```yaml
---
name: my-billing-pipeline-agent
description: Project-specific agent for the billing data domain
tools: [Read, Write, Edit, Bash]
---

# Billing Pipeline Agent

Specialized for our billing data flows from Stripe → Snowflake → revenue marts.
...
```

Custom agents become available immediately to phase commands (`/build` will route work to them when their description matches the task).

## What This Doesn't Change

- **The router** (`generate-agent-router.py`, `routing.json`) is a build-time artifact for the AgentSpec plugin itself. It doesn't index your local agents — Claude Code's runtime loader handles that.
- **WORKFLOW_CONTRACTS.yaml** still defines the contract between phases. Overriding `build-agent` doesn't change *what* `/build` requires as input or output, only *how* the agent fulfills it.
- **KB domains** are not overridden by this mechanism. To customize KB content, fork the relevant `kb/<domain>/` files into your project and reference them from your override agent.

## Verification

After dropping an override, you can confirm it's active by running the agent and observing the response style. If you want stronger guarantees, add a marker to your override (e.g., a unique opening line in the prompt) and check it appears in the agent's first response.

## Related

- [.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml](../../.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml) — the formal phase contracts
- [.claude/agents/README.md](../../.claude/agents/README.md) — auto-generated quick reference (lives in user projects, not the AgentSpec repo)
- [docs/concepts/README.md](README.md) — overall mental model
