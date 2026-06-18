# Getting Started — Claude Code

> Author: Emerson Antonio · 2026-06-17
>
> Claude Code is the **full-fidelity target** for AgentSpec. Every feature
> ships there: namespaced commands (`/agentspec:*`), local agent overrides,
> hooks, MCP, Judge, and the 24 KB domains.

## 1. Install the plugin

```bash
claude plugin marketplace add luanmorenommaciel/agentspec
claude plugin install agentspec
```

This downloads the published plugin and registers it with your Claude Code
session. Updates land with a single command:

```bash
claude plugin update agentspec
```

## 2. (Optional) Install from a local build

Useful when iterating on the plugin itself.

```bash
git clone https://github.com/luanmorenommaciel/agentspec.git
cd agentspec
make build-all
claude --plugin-dir ./dist/claude
```

`make build-all` rebuilds Claude, Cursor, VS Code + Copilot and MCP. Use
`make build-claude` if you only need Claude Code artifacts.

## 3. First commands

```bash
/agentspec:status                              # project + plugin health
/agentspec:brainstorm "Daily orders pipeline"
/agentspec:schema "Star schema for e-commerce analytics"
/agentspec:data-quality models/staging/stg_orders.sql
```

## 4. Local agent overrides

Drop a file in `.claude/agents/<category>/<agent-name>.md` (same `name:` as
the plugin agent) and Claude Code routes to **your** version. See
[Agent Overrides](../concepts/agent-overrides.md).

## 5. Cross-model verification

Set `OPENROUTER_API_KEY`, then call `/judge <file>` for a second opinion
from a non-Claude model. See [Judge Setup](judge-setup.md).

## 6. MCP companion

If you also use Cursor or VS Code + Copilot, add the AgentSpec MCP server
to bridge KB search, agent routing and Judge into those clients without
re-installing the plugin:

```jsonc
// ~/.claude/mcp.json (or merge into your existing config)
{
  "mcpServers": {
    "agentspec-mcp": {
      "command": "python3",
      "args": ["/path/to/agentspec/dist/mcp/server/agentspec_mcp/__main__.py"],
      "env": {
        "AGENTSPEC_ROOT": "/path/to/agentspec/dist/mcp",
        "AGENTSPEC_RESOURCES": "/path/to/agentspec/dist/mcp/resources"
      }
    }
  }
}
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `agentspec` not listed in `claude plugin list` | Re-run `claude plugin install agentspec` |
| `/judge` fails with exit code 2 | `export OPENROUTER_API_KEY=…` |
| Hooks don't run | Confirm `claude --plugin-dir ./dist/claude` (path is absolute) |
| Agent override not taking effect | Match the `name:` field exactly in frontmatter |
