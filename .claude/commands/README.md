# AgentSpec Commands

**29 slash commands** for the SDD workflow, data engineering, visualization, and developer productivity.

## Workflow Commands (7)

| Command | Phase | Description |
|---------|-------|-------------|
| `/brainstorm` | 0 | Explore ideas through dialogue |
| `/define` | 1 | Capture requirements |
| `/design` | 2 | Create architecture |
| `/build` | 3 | Execute implementation |
| `/ship` | 4 | Archive completed feature |
| `/iterate` | Any | Update documents mid-stream |
| `/create-pr` | Any | Create pull request |

## Data Engineering Commands (8)

| Command | Description | Primary Agent |
|---------|-------------|---------------|
| `/pipeline` | DAG/pipeline scaffolding | pipeline-architect |
| `/schema` | Interactive schema design | schema-designer |
| `/data-quality` | Quality rules generation | data-quality-analyst |
| `/lakehouse` | Table format + catalog guidance | lakehouse-architect |
| `/sql-review` | SQL-specific code review | code-reviewer + sql-optimizer |
| `/ai-pipeline` | RAG/embedding scaffolding | ai-data-engineer |
| `/data-contract` | Contract authoring (ODCS) | data-contracts-engineer |
| `/migrate` | Legacy ETL migration | dbt-specialist + spark-engineer |

See [data-engineering/README.md](data-engineering/README.md) for detailed usage.

## Core Commands (4)

| Command | Description |
|---------|-------------|
| `/meeting` | Meeting transcript analysis |
| `/memory` | Save session insights |
| `/sync-context` | Update CLAUDE.md |
| `/readme-maker` | Generate README |

## Knowledge Commands (1)

| Command | Description |
|---------|-------------|
| `/create-kb` | Create KB domain |

## Review Commands (1)

| Command | Description |
|---------|-------------|
| `/review` | Code review workflow |

## Visual Explainer Commands (8)

Generate self-contained HTML pages for visual documentation. Powered by the `visual-explainer` skill.

| Command | Description |
|---------|-------------|
| `/generate-web-diagram` | Generate standalone HTML diagram |
| `/generate-slides` | Magazine-quality slide deck as HTML |
| `/generate-visual-plan` | Visual implementation plan with state machines |
| `/diff-review` | Before/after architecture comparison |
| `/plan-review` | Current codebase vs. proposed plan |
| `/project-recap` | Project state, decisions, and cognitive debt |
| `/fact-check` | Verify document accuracy against codebase |
| `/share` | Share HTML page via Vercel |

See [visual-explainer/](visual-explainer/) for detailed usage.

## Usage

Commands are invoked in Claude Code:

```bash
# SDD workflow
claude> /define USER_AUTH

# Data engineering
claude> /pipeline "Daily orders ETL from Postgres to Snowflake"
claude> /schema "Star schema for e-commerce analytics"
claude> /sql-review models/staging/

# Visual explainer
claude> /generate-web-diagram "Data pipeline architecture"
claude> /generate-slides "AgentSpec overview for stakeholders"
claude> /diff-review main
```
