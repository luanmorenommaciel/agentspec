# Contributing to AgentSpec

Thank you for your interest in AgentSpec! This guide will help you contribute effectively.

## Quick Start

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/agentspec.git
cd agentspec
git checkout -b feature/your-feature

# The framework lives in .claude/
ls .claude/agents/      # 58 specialized agents
ls .claude/commands/    # 31 slash commands
ls .claude/skills/      # 3 capability packs (+ 2 plugin-only skills)
ls .claude/sdd/         # SDD framework
ls .claude/kb/          # Knowledge Base
```

## Ways to Contribute

| Type           | Where                          | Guide                                    |
|----------------|--------------------------------|------------------------------------------|
| New Agent      | `.claude/agents/{category}/`   | [Adding Agents](#adding-a-new-agent)     |
| New KB Domain  | `.claude/kb/{domain}/`         | [Adding KB Domains](#adding-a-kb-domain) |
| New Command    | `.claude/commands/{category}/` | [Adding Commands](#adding-a-command)     |
| New Skill      | `.claude/skills/{skill}/`      | [Adding Skills](#adding-a-skill)         |
| Bug Fix        | Any file                       | [Bug Fixes](#bug-fixes)                  |
| Documentation  | `docs/`                        | [Docs Guide](#documentation)             |

## Adding a New Agent

1. Copy the template:

   ```bash
   cp .claude/agents/_template.md .claude/agents/{category}/your-agent.md
   ```

2. Fill in the required sections:
   - **Identity block** — name, domain, trigger threshold
   - **Capabilities** — what the agent does (2-8 capabilities)
   - **Quality gate** — pre-flight checklist
   - **Response format** — expected output structure
   - **Anti-patterns** — what to avoid

3. Choose the right category:
   - `workflow/` — SDD phase agents
   - `architect/` — system-level design and architecture
   - `cloud/` — AWS, GCP, CI/CD, deployment
   - `platform/` — Microsoft Fabric specialists
   - `python/` — code quality, prompts, documentation
   - `test/` — testing, data quality, data contracts
   - `data-engineering/` — DE implementation specialists
   - `dev/` — developer productivity tools

4. Test with Claude Code:

   ```bash
   # Verify agent is discoverable
   claude> "What agents are available?"
   ```

## Adding a KB Domain

Use the built-in command:

```bash
claude> /create-kb redis
```

Or create manually:

```text
.claude/kb/your-domain/
├── index.md              # Domain overview
├── quick-reference.md    # Cheat sheet (max 100 lines)
├── concepts/             # Core concepts (max 150 lines each)
│   └── your-concept.md
└── patterns/             # Implementation patterns (max 200 lines each)
    └── your-pattern.md
```

Templates are in `.claude/kb/_templates/`. Register your domain in `.claude/kb/_index.yaml`.

## Adding a Command

1. Create `.claude/commands/{category}/your-command.md`
2. Include YAML frontmatter:

   ```yaml
   ---
   name: your-command
   description: What this command does
   ---
   ```

3. Reference the appropriate agent if applicable
4. Test: `claude> /your-command`

## Adding a Skill

Skills are reusable capability packs that power slash commands with templates, references, and scripts.

1. Create a directory: `.claude/skills/your-skill/`
2. Add a `SKILL.md` with YAML frontmatter (`name`, `description`)
3. Add supporting files:
   - `references/` — reference docs and patterns
   - `templates/` — output templates
   - `scripts/` — automation scripts (optional)
4. Create corresponding commands in `.claude/commands/your-skill/`

See existing skills (`visual-explainer`, `excalidraw-diagram`) for examples.

## Bug Fixes

1. Check [existing issues](https://github.com/luanmorenommaciel/agentspec/issues)
2. Create a branch: `git checkout -b fix/description`
3. Make your fix
4. Submit a PR with a clear description of the problem and solution

## Documentation

- Keep markdown files ATX-style (`#`, `##`, `###`)
- Use fenced code blocks with language identifiers
- Keep tables properly aligned
- Test all links before submitting

## Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make changes following the style guidelines above
4. Test with Claude Code to ensure commands and agents work
5. Submit a PR with:
   - Clear title (e.g., "Add redis KB domain" or "Fix brainstorm agent quality gate")
   - Description of what changed and why
   - Link to related issue if applicable

## Plugin Development

AgentSpec is distributed natively to **Claude Code**, **Cursor**, and
**VS Code + Copilot**, plus a universal **AgentSpec MCP** server. The
source of truth is `.claude/`; every distribution is generated from it.

### Workflow

1. **Develop in `.claude/`** — agents, commands, skills, KB, SDD.
2. **Run the multi-target build**:

   ```bash
   make build-all          # Claude Code, Cursor, VS Code + Copilot, MCP
   make validate-all       # sanity-check every dist/ target
   ```

3. **Test locally**:
   - Claude Code → `claude --plugin-dir ./dist/claude`
   - Cursor → copy `dist/cursor/` to `~/.cursor/plugins/local/agentspec/`
   - VS Code + Copilot → point `chat.pluginLocations` at `dist/vscode-copilot/`
   - MCP client → point your client at `dist/mcp/mcp.json`

4. **Iterate** — make changes in `.claude/`, rebuild, reload.

### Build Targets

| Target | Output | Builder |
|--------|--------|---------|
| Claude Code | `dist/claude/` | `make build-claude` (or legacy `bash build-plugin.sh`) |
| Cursor | `dist/cursor/` | `make build-cursor` |
| VS Code + Copilot | `dist/vscode-copilot/` | `make build-copilot` |
| AgentSpec MCP | `dist/mcp/` | `make build-mcp` |
| All four | `dist/` | `make build-all` |

The orchestrator lives in `scripts/build_all.py`; each per-platform
builder is a small Python module that consumes the shared library at
`scripts/lib/` (`platforms.py`, `path_rewrite.py`, `frontmatter.py`,
`packaging.py`).

### Key Concepts

- **`.claude/`** contains agents, commands, skills, KB, SDD — your development environment.
- **`plugin/`** is the legacy Claude-only output (kept for backwards compatibility with users who run `bash build-plugin.sh`).
- **`dist/`** is the new multi-platform output (Claude / Cursor / Copilot / MCP).
- **`plugin-extras/`** contains plugin-only content (skills, hooks, scripts) that ships with every target.
- **`packages/agentspec-mcp/`** is the MCP server source, vendored into `dist/mcp/server/` at build time.

### Path Convention

In `.claude/` (source), reference paths as `.claude/kb/dbt/index.md`. The
build rewrites them per platform:

| Platform | Token |
|----------|-------|
| Claude Code | `${CLAUDE_PLUGIN_ROOT}/kb/dbt/index.md` |
| Cursor | `${PLUGIN_ROOT}/kb/dbt/index.md` |
| VS Code + Copilot | `${CLAUDE_PLUGIN_ROOT}/kb/dbt/index.md` (Claude-format mirror) |
| MCP | `${AGENTSPEC_ROOT}/resources/kb/dbt/index.md` |

Workspace output paths (`.claude/sdd/features/`, `.claude/sdd/reports/`,
`.claude/sdd/archive/`, `.claude/storage/`, `.claude/CLAUDE.md`) stay
literal across every target — they point to the **user's project**, not
the plugin.

### Adding Plugin-Only Content

If you create something that only exists in distribution bundles (not in
`.claude/`), add it to `plugin-extras/`:

- New skills → `plugin-extras/skills/{skill-name}/SKILL.md`
- Hooks → `plugin-extras/hooks/hooks.json`
- Scripts → `plugin-extras/scripts/{script-name}.sh`

`plugin-extras/` is merged into Claude, Cursor and Copilot bundles. The
MCP target ships only the source `.claude/` skills (no plugin-extras).

### Testing

Run the full test suite (78 tests) plus the per-target snapshot tests:

```bash
make test                # alias for python3 -m pytest tests/ -v
make validate-all        # build + validate every dist/ target
```

CI runs `.github/workflows/multi-platform-validate.yml` on every PR
touching `.claude/`, `scripts/`, `tests/`, `packages/`, `plugin-extras/`
or build entrypoints.

## Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/). Be respectful, constructive, and inclusive.

## Questions?

- [Open an issue](https://github.com/luanmorenommaciel/agentspec/issues)
- [Start a discussion](https://github.com/luanmorenommaciel/agentspec/discussions)
