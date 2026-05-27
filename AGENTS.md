# AgentSpec — OpenCode

> See [CLAUDE.md](CLAUDE.md) for full project context, coding standards, and agent catalog.

## OpenCode Plugin Structure

- `.opencode/agents/` — 58 subagents (architect, cloud, platform, python, test, data-engineering, dev, workflow)
- `.opencode/commands/` — 31 slash commands (workflow, data-engineering, core, knowledge, review, visual-explainer)
- `.opencode/skills/` — 5 skills (visual-explainer, excalidraw-diagram, agent-router, sdd-workflow, data-engineering-guide)
- `.opencode/plugins/init-workspace.js` — Session init plugin

## Build

```bash
make build-opencode    # regenerate .opencode/ from .claude/ source
make test-opencode     # run OpenCode compat tests
make check-opencode    # run all checks
```
