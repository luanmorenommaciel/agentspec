# Getting Started — VS Code + Copilot

> Author: Emerson Antonio · 2026-06-17
>
> VS Code 1.110+ ships the **Agent Plugins (Preview)** feature, which
> auto-detects Claude-format plugin manifests. AgentSpec uses this path
> to install on Copilot without rewriting the existing plugin tree, while
> also providing workspace-only fallbacks (`.github/prompts/`,
> `.github/agents/`) for users who can't enable plugins yet.

## 1. Build the Copilot distribution

```bash
git clone https://github.com/luanmorenommaciel/agentspec.git
cd agentspec
make build-copilot         # → dist/vscode-copilot/
```

## 2. Enable Agent Plugins in VS Code

1. Update VS Code to ≥ 1.110.
2. Open `Settings → Extensions → GitHub Copilot Chat`.
3. Enable `chat.plugins.enabled`.
4. Recommended: enable `chat.useCustomizationsInParentRepositories`.

## 3. Install AgentSpec as a Copilot Agent Plugin

Open `~/.vscode/settings.json` (or the workspace-level `.vscode/settings.json`)
and add:

```jsonc
{
  "chat.plugins.enabled": true,
  "chat.pluginLocations": {
    "/abs/path/to/agentspec/dist/vscode-copilot": true
  }
}
```

A starter file is generated at
`dist/vscode-copilot/.vscode/settings.recommended.json`.

Restart VS Code. Open the Copilot Chat panel. `/define`, `/design`,
`/build`, `/pipeline`, `/schema` and every other AgentSpec command
become available. Workflow agents (e.g. `define-agent`) expose handoff
buttons (`Continue with design-agent`) so the SDD flow stays native.

## 4. Workspace-only fallback (no plugin required)

If you cannot enable Agent Plugins, copy the workspace artifacts into your
project:

```bash
mkdir -p .github
cp -r dist/vscode-copilot/.github/prompts .github/
cp -r dist/vscode-copilot/.github/agents  .github/
```

Copilot Chat now exposes:

- `.prompt.md` files at `.github/prompts/` as slash commands
  (`/define`, `/design`, …)
- `.agent.md` files at `.github/agents/` as custom Copilot agents with
  SDD handoffs

This works in any VS Code Copilot version that supports custom agents.

## 5. Enable the AgentSpec MCP companion (recommended)

The MCP companion adds KB search, agent routing, SDD status and Judge to
Copilot. Generate it once:

```bash
make build-mcp             # → dist/mcp/
```

Add to your VS Code settings:

```jsonc
{
  "chat.mcp.servers": {
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

## 6. First commands

```text
/define Daily orders ETL from Postgres to Snowflake
/design ORDERS_PIPELINE
/build ORDERS_PIPELINE
```

## Known limitations

- VS Code Agent Plugins are still marked **Preview**. The schema may
  evolve; if it does, the AgentSpec build adapter will need a refresh.
- Copilot does not currently expose the `/agentspec:` namespace; commands
  surface as flat names just like in Cursor.
- The workspace fallback (`.github/prompts/`, `.github/agents/`) ships
  inside the same `dist/vscode-copilot/` artifact, so you can choose the
  install mode that fits your team without rebuilding.
