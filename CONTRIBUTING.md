# Contributing to AgentSpec

Thank you for contributing! Please read our Code of Conduct first.

## Ways to Contribute

| Type | Description |
|------|-------------|
| Bug Fix | Fix issues in core framework |
| New Agent | Add a specialized agent |
| New KB Domain | Add a knowledge base domain |
| Documentation | Improve or expand docs |
| Examples | Add usage examples |

## Getting Started

```bash
git clone https://github.com/YOUR_ORG/agentspec.git
cd agentspec
git checkout -b feature/your-feature
```

## Adding a New Agent

1. Create `agents/{category}/your-agent.md`
2. Follow the agent template structure
3. Add documentation
4. Submit PR

## Adding a KB Domain

1. Create `kb/your-domain/` with:
   - `index.md`
   - `quick-reference.md`
   - `concepts/` folder
   - `patterns/` folder
2. Use templates from `kb/_templates/`

## Pull Request Process

1. Fork and create a feature branch
2. Make changes following style guidelines
3. Test with Claude Code
4. Submit PR with description

## Style Guidelines

- Use ATX-style headers
- Include code examples
- Keep explanations concise

Thank you for contributing!
