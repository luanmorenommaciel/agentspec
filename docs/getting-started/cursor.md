# Getting Started — Cursor

> Author: Emerson Antonio · 2026-06-17
>
> Cursor receives the same 58 agents, 31 commands and 24 KB domains, with
> two adaptations: each command is also emitted as a Cursor skill (so
> `/define`, `/build`, … work natively), and the plugin manifest is
> declared in both `.cursor-plugin/` and `.claude-plugin/` for portability.

## 1. Build the Cursor distribution

```bash
git clone https://github.com/luanmorenommaciel/agentspec.git
cd agentspec
make build-cursor          # → dist/cursor/
```

If you already built every target with `make build-all`, the Cursor bundle
is already at `dist/cursor/`.

## 2. Install locally

```bash
mkdir -p ~/.cursor/plugins/local
cp -r dist/cursor ~/.cursor/plugins/local/agentspec
```

Restart Cursor. Open the Plugins panel and confirm `agentspec` is listed.
Slash commands (`/define`, `/design`, `/build`, …) become available
immediately. There is **no `/agentspec:` namespace in Cursor** — the
plugin is loaded as a flat set of skills and agents.

## 3. Enable the AgentSpec MCP companion (recommended)

```bash
make build-mcp             # → dist/mcp/
```

Edit Cursor's MCP config (`Settings → Features → Model Context Protocol`)
and add:

```jsonc
{
  "mcpServers": {
    "agentspec-mcp": {
      "command": "python3",
      "args": ["/abs/path/to/agentspec/dist/mcp/server/agentspec_mcp/__main__.py"],
      "env": {
        "AGENTSPEC_ROOT": "/abs/path/to/agentspec/dist/mcp",
        "AGENTSPEC_RESOURCES": "/abs/path/to/agentspec/dist/mcp/resources"
      }
    }
  }
}
```

This enables KB search (`kb_search`), agent routing (`route_agent`), SDD
status (`sdd_status`) and Judge (`judge`) directly inside Cursor's chat.

## 4. First commands

```bash
/define "Daily orders ETL from Postgres to Snowflake"
/design ORDERS_PIPELINE
/build ORDERS_PIPELINE
```

You can also call agents directly from the agents panel. Agent frontmatter
keeps `name`, `description`, `model`, and `tools`; richer metadata
(`tier`, `kb_domains`, `escalation_rules`) lives in the body of the prompt
so the agent still benefits from KB-first resolution.

## 5. SDD outputs

The hooks bundled at `dist/cursor/hooks/hooks.json` create
`.claude/sdd/{features,reports,archive}/` in your workspace on first run
— exactly the same layout Claude Code uses. This means a feature spec
created in Cursor can be re-opened from Claude Code (and vice versa)
without translation.

## Known limitations

- Cursor does not currently support the `/agentspec:` namespace; commands
  appear as flat names. If multiple plugins ship a `/define`, Cursor
  resolves by load order — keep AgentSpec first in your plugin list.
- Hooks rely on bash + Python 3.10+ in the local environment.
- The AgentSpec MCP companion is the recommended way to surface Judge and
  KB routing in Cursor — those are not native slash commands.
