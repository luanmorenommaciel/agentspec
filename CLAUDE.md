# AgentSpec Development

> Developing the Spec-Driven Development framework for Claude Code

---

## Project Context

**What is AgentSpec?** A Claude Code plugin that provides structured AI-assisted development through a 5-phase SDD workflow.

**Current Status:** Initial repository setup complete, ready for enhancement and sanitization.

---

## Repository Structure

```
agentspec/
├── .claude/                 # Claude Code integration (symlinks to root)
│   ├── agents -> ../agents
│   ├── commands -> ../commands
│   ├── sdd -> ../sdd
│   └── kb -> ../kb
│
├── .claude-plugin/          # Plugin manifest
│   └── plugin.json
│
├── agents/                  # 18 specialized agents
│   ├── workflow/            # 6 SDD phase agents
│   ├── code-quality/        # 6 code excellence agents
│   ├── communication/       # 3 explanation agents
│   └── exploration/         # 2 codebase agents
│
├── commands/                # 14 slash commands
│   ├── workflow/            # SDD commands
│   ├── core/                # Utility commands
│   ├── knowledge/           # KB commands
│   └── review/              # Review commands
│
├── sdd/                     # SDD framework
│   ├── architecture/        # Framework design
│   ├── templates/           # Document templates
│   ├── examples/            # Example workflow
│   ├── features/            # Active development
│   ├── reports/             # Build reports
│   └── archive/             # Shipped features
│
├── kb/                      # Knowledge Base
│   ├── _templates/          # KB domain templates
│   └── pydantic/            # Example domain
│
├── docs/                    # Documentation
└── examples/                # Usage examples
```

---

## Development Workflow

Use AgentSpec's own SDD workflow to develop AgentSpec:

```bash
# Explore an enhancement idea
/brainstorm "Add Judge layer for spec validation"

# Capture requirements
/define JUDGE_LAYER

# Design the architecture
/design JUDGE_LAYER

# Build it
/build JUDGE_LAYER

# Ship when complete
/ship JUDGE_LAYER
```

---

## Active Development Tasks

| Task | Status | Description |
|------|--------|-------------|
| Sanitize agents | Pending | Remove project-specific references |
| Create CLAUDE.md.template | Pending | Template for user projects |
| Add more KB domains | Pending | React, TypeScript, etc. |
| Implement Judge layer | Planned | Spec validation via external LLM |
| Add telemetry | Planned | Local usage tracking |

---

## Coding Standards

### Markdown Files

- ATX-style headers (`#`, `##`, `###`)
- Fenced code blocks with language identifiers
- Tables properly aligned

### Agent Prompts

- Specific trigger conditions
- Clear capabilities list
- Concrete examples
- Defined output format

### KB Domains

- `index.md` - Domain overview
- `quick-reference.md` - Cheat sheet
- `concepts/` - 3-6 concept files
- `patterns/` - 3-6 pattern files with code examples

---

## Commands Available

| Command | Purpose |
|---------|---------|
| `/brainstorm` | Explore ideas |
| `/define` | Capture requirements |
| `/design` | Create architecture |
| `/build` | Execute implementation |
| `/ship` | Archive completed work |
| `/iterate` | Update existing docs |
| `/create-kb` | Create KB domain |
| `/review` | Code review |

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `.claude-plugin/plugin.json` | Plugin manifest for Claude Code |
| `sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Phase transition rules |
| `sdd/templates/*.md` | Document templates |
| `kb/_templates/*.template` | KB domain templates |

---

## Version

- **Version:** 1.0.0
- **Status:** Development
- **Last Updated:** 2026-02-03
