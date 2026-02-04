---
name: sync-context
description: Sync project context to CLAUDE.md by analyzing codebase patterns and conventions
---

# Sync Context Command

Analyzes codebase and intelligently updates `.claude/CLAUDE.md` with current project context.

## Usage

```bash
/sync-context                    # Full analysis and update
/sync-context --section agents   # Update specific section
/sync-context --dry-run          # Preview changes without saving
```

---

## What It Does

1. **Analyzes** current codebase structure
2. **Extracts** patterns, conventions, and architecture
3. **Merges** with existing CLAUDE.md content
4. **Preserves** manual customizations
5. **Updates** sections that need refresh

---

## Analysis Process

### Step 1: Scan Codebase Structure

```text
# Discover project structure
Glob("**/*.py")              # Python files
Glob("**/*.ts")              # TypeScript files
Glob("**/package.json")      # Node projects
Glob("**/pyproject.toml")    # Python projects
Glob("**/Dockerfile")        # Container configs
Glob("**/*.tf")              # Terraform
```

### Step 2: Extract Patterns

```text
# Code patterns
Grep("@dataclass")           # Dataclass usage
Grep("class.*Parser")        # Parser patterns
Grep("def test_")            # Test patterns
Grep("async def")            # Async patterns

# Architecture patterns
Grep("from src")             # Import structure
Grep("@router")              # API patterns
Grep("@lambda_handler")      # Lambda patterns
```

### Step 3: Analyze Agents

```text
# List available agents
Glob(".claude/agents/**/*.md")

# Categorize by folder
- workflow/      → SDD pipeline agents
- code-quality/  → Review, clean, test
- data-engineering/ → Spark, Lakeflow
- aws/           → Lambda, deployer
- ai-ml/         → LLM, prompts
- domain/        → Project-specific
```

### Step 4: Merge Updates

```text
# Sections to update
- Project Structure (from scan)
- Coding Standards (from patterns)
- Agent Usage (from agent analysis)
- Commands (from commands/)
- Environment (from config files)

# Sections to preserve
- Project Context (manual)
- Core Mission (manual)
- Important Dates (manual)
- Getting Help (manual)
```

---

## CLAUDE.md Template

Generated CLAUDE.md follows this structure:

```markdown
# {Project Name}

## Project Context

{Manual: What this project does and why}

---

## Architecture Overview

{Auto-generated from codebase scan}

```text
{Data flow diagram}
```

| Stage | Technology | Purpose |
| ----- | ---------- | ------- |
| {stage} | {tech} | {purpose} |

---

## Project Structure

{Auto-generated from Glob scans}

```text
{project}/
├── src/
│   ├── {folders discovered}
├── tests/
├── .claude/
│   ├── agents/
│   ├── commands/
│   ├── sdd/
│   ├── kb/
│   └── memories/
```

---

## Agent Usage Guidelines

{Auto-generated from agents/ folder}

### Available Agents by Category

| Category | Agents | Use When |
| -------- | ------ | -------- |
| Workflow | prd-agent, clarify-agent, ... | Building features with SDD |
| Code Quality | code-reviewer, test-generator, ... | Improving code |
| {category} | {agents} | {trigger} |

---

## Coding Standards

{Auto-generated from detected patterns}

### Language: {Python/TypeScript/etc}

- **Version:** {detected from config}
- **Style:** {detected patterns}
- **Testing:** {detected framework}

### Detected Patterns

| Pattern | Usage | Example File |
| ------- | ----- | ------------ |
| {pattern} | {where used} | {file path} |

---

## Commands

{Auto-generated from commands/ folder}

| Command | Purpose |
| ------- | ------- |
| /build-feature | Full SDD pipeline |
| /memory | Save session insights |
| {command} | {purpose} |

---

## Environment Variables

{Auto-generated from .env.example, config files}

| Variable | Purpose |
| -------- | ------- |
| {var} | {purpose} |

---

## MCP Tools Available

{Auto-generated from settings}

| MCP Server | Purpose |
| ---------- | ------- |
| context7-mcp | Library documentation |
| exa | Code context search |
| {mcp} | {purpose} |

---

## Important Dates

{Manual: Project-specific dates}

---

## Getting Help

{Auto-generated from structure}

- **Documentation**: Start with relevant docs
- **Agents**: Review .claude/agents/
- **Commands**: Use /help for available commands
```

---

## Section Update Rules

| Section | Source | Update Mode |
| ------- | ------ | ----------- |
| Project Context | Manual | Preserve |
| Architecture | Codebase scan | Replace |
| Project Structure | Glob patterns | Replace |
| Agent Usage | agents/ folder | Replace |
| Coding Standards | Pattern detection | Merge |
| Commands | commands/ folder | Replace |
| Environment | Config files | Merge |
| MCP Tools | settings.json | Replace |
| Important Dates | Manual | Preserve |
| Getting Help | Structure | Replace |

**Replace**: Fully regenerate from source
**Merge**: Add new, preserve custom
**Preserve**: Never auto-modify

---

## Execution Flow

```text
1. Read existing CLAUDE.md
   │
   ▼
2. Parse into sections
   │
   ▼
3. Analyze codebase (parallel)
   ├── Glob for structure
   ├── Grep for patterns
   ├── Read config files
   └── List agents/commands
   │
   ▼
4. Generate new sections
   │
   ▼
5. Apply update rules
   ├── Replace auto sections
   ├── Merge semi-auto sections
   └── Preserve manual sections
   │
   ▼
6. Validate (dry-run or save)
   │
   ▼
7. Write updated CLAUDE.md
```

---

## Example Output

```text
UPDATE CLAUDE.MD
━━━━━━━━━━━━━━━━

Analyzing codebase...
✓ Found 47 Python files
✓ Found 12 test files
✓ Found 28 agents
✓ Found 8 commands

Detected patterns:
✓ Dataclass pattern (15 usages)
✓ Parser pattern (4 files)
✓ Generator pattern (8 usages)

Section updates:
• Architecture: UPDATED (new components detected)
• Project Structure: UPDATED (3 new folders)
• Agent Usage: UPDATED (2 new agents)
• Coding Standards: MERGED (1 new pattern)
• Commands: UPDATED (1 new command)
• Project Context: PRESERVED (manual content)

━━━━━━━━━━━━━━━━
CLAUDE.md updated successfully
```

---

## Flags

| Flag | Description |
| ---- | ----------- |
| `--dry-run` | Preview changes without saving |
| `--section {name}` | Update only specific section |
| `--force` | Replace all sections (ignores preserve rules) |
| `--verbose` | Show detailed analysis |

---

## Best Practices

### When to Run

- After adding new agents or commands
- After significant architecture changes
- After adding new file types
- When onboarding new team members

### What to Customize

After running, manually update:

1. **Project Context** - Add business context
2. **Important Dates** - Add milestone dates
3. **Architecture** - Add business-specific details
4. **Coding Standards** - Add team conventions

### Version Control

```bash
# Review changes before committing
git diff .claude/CLAUDE.md

# Commit with context
git add .claude/CLAUDE.md
git commit -m "chore: update CLAUDE.md with latest project structure"
```
