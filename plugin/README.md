# AgentSpec Plugin

**Spec-Driven Development for Data Engineering on Claude Code**

58 agents | 24 KB domains | 31 commands | 16 skills | 5-phase SDD workflow

## Install

```bash
claude plugin marketplace add luanmorenommaciel/agentspec
claude plugin install agentspec
```

## What You Get

### 5-Phase SDD Workflow

```
/agentspec:brainstorm → /agentspec:define → /agentspec:design → /agentspec:build → /agentspec:ship
```

### Data Engineering Commands

| Command | Purpose |
|---------|---------|
| `/agentspec:pipeline` | DAG/pipeline scaffolding |
| `/agentspec:schema` | Interactive schema design |
| `/agentspec:data-quality` | Quality rules generation |
| `/agentspec:sql-review` | SQL optimization review |
| `/agentspec:lakehouse` | Table format + catalog guidance |
| `/agentspec:ai-pipeline` | RAG/embedding scaffolding |
| `/agentspec:data-contract` | Data contract authoring (ODCS) |
| `/agentspec:migrate` | Legacy ETL migration |

### 58 Specialized Agents

| Category | Count | Examples |
|----------|-------|---------|
| Architect | 8 | schema-designer, pipeline-architect, genai-architect |
| Cloud | 10 | aws-lambda-architect, gcp-data-architect, ci-cd-specialist |
| Data Engineering | 15 | dbt-specialist, spark-engineer, airflow-specialist |
| Platform | 6 | fabric-architect, fabric-pipeline-developer |
| Python | 6 | python-developer, code-reviewer, ai-prompt-specialist |
| Workflow | 6 | brainstorm-agent, define-agent, build-agent |
| Dev | 4 | codebase-explorer, prompt-crafter, meeting-analyst |
| Test | 3 | test-generator, data-quality-analyst, data-contracts-engineer |

### 24 Knowledge Base Domains

dbt, Spark, Airflow, streaming, SQL patterns, data modeling, data quality, medallion, lakehouse, cloud platforms, AWS, GCP, Microsoft Fabric, Lakeflow, Terraform, AI data engineering, GenAI, prompt engineering, modern stack, Pydantic, Python, testing, Supabase, shared anti-patterns

### 16 Auto-Invoked Skills

- **sdd-workflow** -- umbrella guide for the 5-phase development workflow
- **sdd-brainstorm / sdd-define / sdd-design / sdd-build / sdd-ship / sdd-iterate** -- per-phase SDD methodology, loaded by the thin phase agents and commands
- **component-model** -- decides which layer new logic belongs to (agent/skill/command/KB) + fat-to-thin refactoring
- **data-engineering-guide** -- routes to the right agent for DE tasks
- **visual-explainer** -- generates visual HTML diagrams and slide decks
- **excalidraw-diagram** -- creates Excalidraw diagram JSON files
- **agent-router** -- auto-matches tasks to the best specialist agent
- **github-cr-adr** -- drafts an ADR with a worthiness gate and pre-draft dedup
- **github-cr-issue** -- drafts typed issues (feature/component/task/bug/spike) from templates
- **github-post-issue** -- guarded gh publishing: label validation, sub-issues, close-never-delete
- **kb-build** -- high-assurance, source-verified knowledge-base building (via `/create-kb --validated`)

## Requirements

- Claude Code v1.0.33+
- No external dependencies

## License

MIT
