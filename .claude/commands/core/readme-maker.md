---
name: readme-maker
description: Generate comprehensive, production-ready README.md by analyzing codebase with explorer + documenter agents
---

# README Maker Command

Generates a professional README.md by combining codebase exploration with documentation best practices.

## Usage

```bash
/readme-maker                        # Full analysis → README.md
/readme-maker --output docs/         # Output to specific directory
/readme-maker --style minimal        # Minimal README (Quick Start focus)
/readme-maker --style comprehensive  # Full documentation (default)
/readme-maker --dry-run              # Preview without saving
```

---

## What It Does

1. **Explores** codebase using codebase-explorer patterns
2. **Analyzes** project structure, tech stack, and patterns
3. **Generates** README.md following code-documenter standards
4. **Validates** all examples and links before saving

---

## Execution Flow

```text
┌─────────────────────────────────────────────────────────────┐
│  README-MAKER WORKFLOW                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: EXPLORE (codebase-explorer patterns)              │
│  ├─ Scan root structure (ls, package files, configs)        │
│  ├─ Map source code (Glob patterns by language)             │
│  ├─ Identify tech stack and frameworks                      │
│  ├─ Count files, tests, documentation                       │
│  └─ Calculate health score                                  │
│                                                             │
│  Phase 2: EXTRACT (project metadata)                        │
│  ├─ Read package.json / pyproject.toml / Cargo.toml         │
│  ├─ Parse existing README (if present)                      │
│  ├─ Detect entry points (main, index, handler)              │
│  ├─ Find installation/setup commands                        │
│  └─ Identify environment variables                          │
│                                                             │
│  Phase 3: GENERATE (code-documenter patterns)               │
│  ├─ Create compelling project description                   │
│  ├─ Build Quick Start with tested commands                  │
│  ├─ Document features with examples                         │
│  ├─ Add architecture overview (if complex)                  │
│  └─ Include contributing guidelines                         │
│                                                             │
│  Phase 4: VALIDATE (quality checks)                         │
│  ├─ Test all installation commands                          │
│  ├─ Verify code examples work                               │
│  ├─ Check all links resolve                                 │
│  └─ Ensure no placeholder text remains                      │
│                                                             │
│  Phase 5: OUTPUT                                            │
│  ├─ Write README.md to project root                         │
│  └─ Report summary of what was generated                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Analysis Steps

### Step 1: Scan Project Structure

```text
# Root structure
ls -la (root)
Read README.md (if exists - preserve manual content)

# Package files (detect language/framework)
Glob("**/package.json")      # Node.js
Glob("**/pyproject.toml")    # Python
Glob("**/Cargo.toml")        # Rust
Glob("**/go.mod")            # Go
Glob("**/pom.xml")           # Java/Maven
Glob("**/build.gradle")      # Java/Gradle

# Source code
Glob("src/**/*")             # Main source
Glob("lib/**/*")             # Library code
Glob("tests/**/*")           # Test files
Glob("docs/**/*")            # Documentation
```

### Step 2: Extract Project Metadata

```text
# From package files
- Project name
- Version
- Description
- Author/maintainers
- License
- Dependencies (key ones)
- Scripts/commands

# From codebase
- Primary language
- Framework(s)
- Entry points
- Environment variables (from .env.example, config)
- API endpoints (if applicable)
```

### Step 3: Generate README Sections

Use this template structure:

```markdown
# {Project Name}

> {Compelling one-line description from package or inferred}

{Badges: build status, version, license}

## Overview

{2-3 paragraphs explaining:}
- What the project does
- Why it exists (problem it solves)
- Who it's for

## Features

{Bullet list with brief descriptions}
- Feature 1: Description
- Feature 2: Description

## Quick Start

{60-second setup - MUST be tested commands}

### Prerequisites

- {requirement 1}
- {requirement 2}

### Installation

```bash
{installation commands}
```

### Basic Usage

```bash
{usage example}
```

## Documentation

{Table linking to detailed docs if they exist}

| Topic | Link |
| ----- | ---- |
| API Reference | [docs/api.md](docs/api.md) |
| Configuration | [docs/config.md](docs/config.md) |

## Architecture

{Only include if project is complex enough}

```text
{Simple ASCII diagram}
```

## Configuration

{Environment variables and config options}

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `VAR_NAME` | What it does | `default` |

## Development

### Setup

```bash
{dev setup commands}
```

### Running Tests

```bash
{test commands}
```

## Contributing

{Link to CONTRIBUTING.md or brief guidelines}

## License

{License name} - see [LICENSE](LICENSE)
```

---

## Output Styles

### Minimal (`--style minimal`)

Sections included:
- Project name + description
- Quick Start (installation + basic usage)
- License

Best for: Small utilities, scripts, simple libraries

### Comprehensive (`--style comprehensive`) - Default

Sections included:
- All sections in template
- Architecture diagram
- Full configuration reference
- Development guide
- API documentation links

Best for: Production projects, open source, team codebases

---

## Quality Checklist

Before saving README.md, verify:

```text
CONTENT
[ ] Project description is clear and compelling
[ ] Quick Start works (commands tested)
[ ] Features accurately reflect codebase
[ ] No placeholder text like "TODO" or "{}"

FORMAT
[ ] Badges are valid (if included)
[ ] Code blocks have language hints
[ ] Tables properly formatted
[ ] Links point to existing files

ACCURACY
[ ] Version matches package file
[ ] Dependencies are current
[ ] Installation actually works
[ ] Examples produce expected output
```

---

## Example Output

```text
README GENERATION
━━━━━━━━━━━━━━━━━

Exploring codebase...
✓ Detected: Python project (pyproject.toml)
✓ Found: 17 source files, 4 test files
✓ Framework: Click CLI, Pydantic
✓ Entry point: src/invoice_gen/cli.py

Extracting metadata...
✓ Name: invoice-gen
✓ Version: 0.1.0
✓ License: MIT
✓ Dependencies: click, pydantic, faker

Generating README...
✓ Overview: from pyproject.toml description
✓ Quick Start: from scripts + entry point
✓ Features: from module analysis
✓ Configuration: from .env.example

Validating...
✓ Installation commands work
✓ Basic usage example runs
✓ All links valid

━━━━━━━━━━━━━━━━━
Saved: README.md (comprehensive style)

Preview:
# invoice-gen

> Generate synthetic invoices for testing ML extraction pipelines

## Quick Start

pip install -e .
invoice-gen generate --count 10 --output invoices/
```

---

## Flags

| Flag | Description |
| ---- | ----------- |
| `--output {dir}` | Output directory (default: project root) |
| `--style {type}` | `minimal` or `comprehensive` (default) |
| `--dry-run` | Preview without saving |
| `--preserve-manual` | Keep manually-written sections (default: true) |
| `--force` | Overwrite without preserving manual content |

---

## Best Practices

### When to Use

- New projects without README
- Projects with outdated README
- After major refactoring
- Before open-sourcing internal code

### What to Review After

1. **Overview** - Add business context the tool can't infer
2. **Features** - Prioritize and add details
3. **Architecture** - Add domain-specific explanations
4. **Contributing** - Add team-specific guidelines

### Integration with Other Commands

```bash
# Full documentation workflow
/readme-maker                    # Generate README
/sync-context                    # Update CLAUDE.md
/memory "Generated docs"         # Save what was done
```

---

## Agent Integration

This command leverages:

| Agent | Purpose |
| ----- | ------- |
| **codebase-explorer** | Comprehensive codebase analysis |
| **code-documenter** | Documentation generation patterns |

The command combines:
- Explorer's systematic analysis workflow
- Documenter's quality checklist and templates
- Both agents' validation requirements

---

## Remember

> **"A README is often the first impression of your project"**

**Goal:** Generate README that answers:
1. What is this?
2. Why should I care?
3. How do I use it?

**Quality bar:** Every command must work. Every link must resolve. No placeholders allowed.
