# AgentSpec Plugin

**Spec-Driven Development for Data Engineering on Claude Code**

58 agents | 23 KB domains | 30 commands | 5 skills | 5-phase SDD workflow

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

### 23 Knowledge Base Domains

dbt, Spark, Airflow, streaming, SQL patterns, data modeling, data quality, medallion, lakehouse, cloud platforms, AWS, GCP, Microsoft Fabric, Lakeflow, Terraform, AI data engineering, GenAI, prompt engineering, modern stack, Pydantic, Python, testing

### 4 Auto-Invoked Skills

- **sdd-workflow** -- guides through the 5-phase development workflow
- **data-engineering-guide** -- routes to the right agent for DE tasks
- **visual-explainer** -- generates visual HTML diagrams and slide decks
- **excalidraw-diagram** -- creates Excalidraw diagram JSON files

## Requirements

- Claude Code v1.0.33+
- No external dependencies

## License

MIT
