---
name: create-kb
description: Create a KB domain — light single-pass by default, --validated for a source-verified high-assurance build, --audit for KB health
---

# Create Knowledge Base Command

> Single entrypoint for KB domain creation: a light single-pass build by default, a high-assurance source-verified build with `--validated`, and a health audit with `--audit`.

## Usage

```
/create-kb <DOMAIN> [--validated]
/create-kb --audit
```

**Examples**: `/create-kb redis`, `/create-kb pandas --validated`, `/create-kb --audit`

## Choosing the mode

Default (light) suits quick, low-stakes domains where `kb-architect`'s own confidence model suffices. `--validated` suits foundational or high-stakes domains where every claim must be source-cited and independently fact-checked — it costs more tokens and buys assurance. When unsure: if many agents will trust this domain as ground truth, use `--validated`.

## What Happens

**Default (light):**

1. **Validates prerequisites** — checks `_templates/` and `_index.yaml` exist
2. **Invokes the kb-architect agent** — single-pass build with the agent's confidence model
3. **Reports completion** — shows score and files created

**`--validated` (high-assurance):**

1. **Loads the kb-build skill** and follows its six stages — ground → plan → research with adversarial refutation → build via `kb-architect` subagents → independent fact-check gate → additive `_index.yaml` registration
2. **Reports completion** — verification summary, citation coverage, files created

**`--audit`:**

1. **Invokes the kb-architect agent's audit capability** — scores existing domains against the 100-point rubric

## Options

| Command | Action |
|---------|--------|
| `/create-kb <domain>` | Create new KB domain (light, single-pass) |
| `/create-kb <domain> --validated` | Create with source verification: research, adversarial checks, independent fact-check gate |
| `/create-kb --audit` | Audit existing KB health |

## See Also

- **Skill (`--validated` mode)**: `${CLAUDE_PLUGIN_ROOT}/skills/kb-build/SKILL.md`
- **Agent (light mode + audit)**: `${CLAUDE_PLUGIN_ROOT}/agents/architect/kb-architect.md`
- **Templates**: `${CLAUDE_PLUGIN_ROOT}/kb/_templates/`
- **Registry**: `${CLAUDE_PLUGIN_ROOT}/kb/_index.yaml`
