# Getting Started with AgentSpec

Get from zero to your first spec-driven data pipeline in 10 minutes.

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- Git

## Installation

### Option 1: Install as Plugin (Recommended)

```bash
claude plugin marketplace add luanmorenommaciel/agentspec
claude plugin install agentspec
```

Or test locally:

```bash
git clone https://github.com/luanmorenommaciel/agentspec.git
claude --plugin-dir ./agentspec/plugin
```

### Option 2: Copy Framework (Legacy)

```bash
git clone https://github.com/luanmorenommaciel/agentspec.git
cp -r agentspec/.claude your-project/.claude
```

## Initialize Your Project

The SDD directory structure is already set up:

```text
your-project/.claude/
+-- agents/              # 58 specialized agents (ready to use)
|   +-- workflow/        # 6 SDD phase agents
|   +-- architect/       # 8 system-level design agents
|   +-- cloud/           # 10 AWS, GCP, CI/CD agents
|   +-- platform/        # 6 Microsoft Fabric agents
|   +-- python/          # 6 code quality + prompt agents
|   +-- test/            # 3 testing + data quality agents
|   +-- data-engineering/ # 15 DE implementation agents
|   +-- dev/             # 4 developer productivity agents
|
+-- commands/            # 29 slash commands (ready to use)
|   +-- workflow/        # 7 SDD phase commands
|   +-- data-engineering/ # 8 DE commands
|   +-- visual-explainer/ # 8 visual documentation commands
|   +-- core/            # 4 utility commands
|   +-- knowledge/       # 1 KB command
|   +-- review/          # 1 code review command
|
+-- sdd/
|   +-- features/        # Your active feature documents go here
|   +-- reports/         # Build reports land here
|   +-- archive/         # Shipped features archived here
|   +-- templates/       # 5 document templates
|
+-- kb/                  # 23 data engineering KB domains (ready to use)
```

## Your First Data Pipeline (5 minutes)

Let's build an orders pipeline using the full SDD workflow.

### Step 1: Brainstorm (Optional)

Explore your idea through guided dialogue:

```bash
claude> /brainstorm "Daily orders pipeline from Postgres to Snowflake with star schema"
```

AgentSpec asks targeted questions about source systems, volumes, freshness SLAs, and consumer needs. Output: `BRAINSTORM_ORDERS_PIPELINE.md`

### Step 2: Define Requirements

Capture formal requirements with data contracts:

```bash
claude> /define ORDERS_PIPELINE
```

Output: `DEFINE_ORDERS_PIPELINE.md` with:

- Problem statement and users
- Data contract (schema, SLAs, lineage)
- Source inventory (volumes, freshness)
- Clarity Score (must reach 12/15 to proceed)

### Step 3: Design Architecture

Create the pipeline architecture:

```bash
claude> /design ORDERS_PIPELINE
```

Output: `DESIGN_ORDERS_PIPELINE.md` with:

- Architecture diagram with DAG structure
- Partition strategy and incremental approach
- File manifest with agent assignments (@dbt-specialist, @airflow-specialist, @spark-engineer)
- Schema evolution plan
- Data quality gates

### Step 4: Build

Execute the implementation with agent delegation:

```bash
claude> /build ORDERS_PIPELINE
```

AgentSpec delegates dbt models to `@dbt-specialist`, DAGs to `@airflow-specialist`, Spark jobs to `@spark-engineer`, and quality checks to `@data-quality-analyst`. Verification includes `dbt build`, `sqlfluff lint`, and data quality assertions. Output: `BUILD_REPORT_ORDERS_PIPELINE.md`

### Step 5: Ship

Archive everything with lessons learned:

```bash
claude> /ship ORDERS_PIPELINE
```

## Quick Data Engineering Commands

Don't need the full SDD workflow? Use commands directly:

```bash
# Design a star schema
claude> /schema "Star schema for e-commerce analytics"

# Scaffold an Airflow DAG
claude> /pipeline "Daily orders ETL from Postgres to Snowflake"

# Generate quality checks for a model
claude> /data-quality models/staging/stg_orders.sql

# Review SQL for anti-patterns
claude> /sql-review models/marts/

# Migrate legacy stored procedures
claude> /migrate legacy/etl_orders_proc.sql

# Author a data contract
claude> /data-contract "Contract between orders team and analytics"
```

## Customizing Agents

Every team has its own conventions. AgentSpec lets you override any of the 58 plugin agents locally without forking — drop a file with the same name into `.claude/agents/<category>/` and it takes precedence.

When the SessionStart hook runs for the first time, it scaffolds:

```text
.claude/agents/
├── README.md       # auto-generated quick reference
├── workflow/       # override SDD phase agents (build-agent, define-agent, etc.)
└── custom/         # add brand-new project-specific agents
```

To override an agent, copy it from the plugin and edit your local copy:

```bash
cp $CLAUDE_PLUGIN_ROOT/agents/workflow/build-agent.md \
   .claude/agents/workflow/build-agent.md
$EDITOR .claude/agents/workflow/build-agent.md
```

Claude Code's native plugin loader handles precedence — your version wins when names match. See [Agent Overrides](../concepts/agent-overrides.md) for the full pattern, including custom agents and verification.

## What's Next

- [Core Concepts](../concepts/) -- understand how phases, agents, and KB work together
- [Agent Overrides](../concepts/agent-overrides.md) -- customize phase agents to your team's conventions
- [Tutorials](../tutorials/) -- dbt, star schema, data quality, Spark, streaming, RAG walkthroughs
- [Reference](../reference/) -- full command, agent, and KB domain catalog

## Troubleshooting

**Commands not recognized?**
Ensure `.claude/commands/` exists in your project root with the slash command files.

**Agent not matching?**
Check that `.claude/agents/` contains the agent `.md` files. Agents are discovered via glob pattern.

**Clarity score too low?**
The `/define` phase requires 12/15 to proceed. For data pipelines, ensure Source Inventory, Schema Contract, and Freshness SLAs are populated.

**KB domain not loading?**
Check `.claude/kb/_index.yaml` -- the domain must be registered there. All 23 KB domains come pre-configured.
