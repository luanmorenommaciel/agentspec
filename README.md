<div align="center">

# AgentSpec

### Spec-Driven Development for Claude Code

**Transform ideas into shipped features through a structured 5-phase AI workflow**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg)](https://claude.ai/code)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](CHANGELOG.md)

[Quick Start](#-quick-start) | [Documentation](docs/) | [Examples](examples/) | [Contributing](CONTRIBUTING.md)

</div>

---

## What is AgentSpec?

AgentSpec is a **Spec-Driven Development (SDD)** framework that brings structure and traceability to AI-assisted software development. Instead of ad-hoc prompting, AgentSpec guides you through a proven 5-phase workflow:

```
/brainstorm  →  /define  →  /design  →  /build  →  /ship
   (Explore)    (Capture)   (Architect)  (Execute)  (Archive)
```

Each phase produces traceable artifacts, ensuring nothing gets lost between idea and implementation.

### Why AgentSpec?

| Problem | AgentSpec Solution |
|---------|-------------------|
| "I forgot what we decided" | Persistent DEFINE docs capture all requirements |
| "The implementation doesn't match the spec" | DESIGN docs provide clear contracts |
| "We keep making the same mistakes" | SHIPPED docs preserve lessons learned |
| "Context gets lost in long sessions" | Structured workflow maintains continuity |
| "No audit trail for AI decisions" | Every phase produces traceable artifacts |

---

## Key Features

### 5-Phase SDD Workflow

| Phase | Command | Purpose | Artifact |
|-------|---------|---------|----------|
| **Brainstorm** | `/brainstorm` | Explore ideas through dialogue | `BRAINSTORM_*.md` |
| **Define** | `/define` | Capture requirements formally | `DEFINE_*.md` |
| **Design** | `/design` | Create technical architecture | `DESIGN_*.md` |
| **Build** | `/build` | Execute implementation | `BUILD_REPORT_*.md` |
| **Ship** | `/ship` | Archive with lessons learned | `SHIPPED_*.md` |

### Specialized Agents (17 included)

| Category | Agents | Purpose |
|----------|--------|---------|
| **Workflow** | 6 | Drive each SDD phase |
| **Code Quality** | 6 | Review, test, document code |
| **Communication** | 3 | Explain, plan, analyze meetings |
| **Exploration** | 2 | Navigate and understand codebases |

### Knowledge Base Framework

Build domain-specific knowledge that grounds AI responses:

```
kb/
├── _templates/           # Create your own KB domains
├── pydantic/            # Example: Data validation patterns
│   ├── concepts/
│   ├── patterns/
│   └── quick-reference.md
```

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_ORG/agentspec.git

# Navigate to your project
cd your-project

# Install as Claude Code plugin
claude --plugin-dir /path/to/agentspec
```

### Your First Feature

```bash
# 1. Start with exploration
claude> /brainstorm "Add user authentication to the app"

# 2. Capture requirements
claude> /define

# 3. Design the architecture
claude> /design

# 4. Build with verification
claude> /build

# 5. Ship and archive
claude> /ship
```

### Project Setup

AgentSpec creates this structure in your project:

```
your-project/
├── .claude/
│   └── sdd/
│       ├── features/     # Active feature documents
│       ├── reports/      # Build reports
│       └── archive/      # Shipped features (lessons learned)
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started/) | Installation and first steps |
| [SDD Workflow](sdd/README.md) | Deep dive into each phase |
| [Agents Reference](agents/README.md) | All 17 agents explained |
| [Commands Reference](commands/README.md) | Slash commands guide |
| [KB Framework](kb/README.md) | Building knowledge bases |
| [Examples](examples/) | Real-world usage examples |

---

## Project Structure

```
agentspec/
├── .claude-plugin/
│   └── plugin.json       # Plugin manifest
│
├── agents/               # 17 specialized agents
│   ├── workflow/         # SDD phase agents
│   ├── code-quality/     # Code review, testing
│   ├── communication/    # Explanation, planning
│   └── exploration/      # Codebase navigation
│
├── commands/             # Slash commands
│   ├── workflow/         # /brainstorm, /define, etc.
│   ├── core/             # /memory, /sync-context
│   ├── knowledge/        # /create-kb
│   └── review/           # /review, /create-pr
│
├── sdd/                  # SDD framework
│   ├── templates/        # Document templates
│   ├── architecture/     # ARCHITECTURE.md, contracts
│   └── examples/         # Complete example flow
│
├── kb/                   # Knowledge Base framework
│   └── _templates/       # KB domain templates
│
├── docs/                 # Extended documentation
└── examples/             # Example projects
```

---

## How It Works

### Phase Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  BRAINSTORM │────▶│   DEFINE    │────▶│   DESIGN    │
│  (Optional) │     │ Requirements│     │Architecture │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    SHIP     │◀────│    BUILD    │◀────│   Agent     │
│   Archive   │     │   Execute   │     │  Matching   │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Agent Matching

When you run `/build`, AgentSpec automatically matches the right agents to your task:

```
DESIGN doc mentions "Pydantic models" + "pytest"
                    │
                    ▼
┌─────────────────────────────────────────┐
│  Agent Router                           │
│  ├── python-developer (Pydantic work)   │
│  ├── test-generator (pytest tests)      │
│  └── code-reviewer (quality check)      │
└─────────────────────────────────────────┘
```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Ways to Contribute

- **New Agents**: Add specialized agents for your domain
- **KB Domains**: Share knowledge base domains
- **Examples**: Document real-world usage
- **Bug Fixes**: Help improve stability
- **Documentation**: Clarify and expand docs

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

AgentSpec was developed as part of a production invoice processing pipeline project, proving its value in real-world AI-assisted development.

---

<div align="center">

**[Documentation](docs/) | [Examples](examples/) | [Contributing](CONTRIBUTING.md) | [Changelog](CHANGELOG.md)**

Built with Claude Code

</div>
