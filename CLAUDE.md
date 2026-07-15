# AgentSpec Development

> Spec-Driven Development framework for Data Engineering on Claude Code

---

## Project Context

**What is AgentSpec?** A Claude Code plugin that provides structured AI-assisted development through a 5-phase SDD workflow, specialized for data engineering with 58 agents, 31 commands, 24 KB domains, and 20 skills (16 distributed in the plugin + 4 repo-local).

**Component model (canonical: `.claude/kb/shared/component-model.md`):**

| Layer | Responsibility |
|---|---|
| Agents | EXECUTION — identity, tool scope, model tier, escalation; thin shells around capabilities |
| Skills | CAPABILITY — the HOW: methodology, specialized knowledge, resource usage |
| Commands | ENTRYPOINT — argument surface, mode selection, sequencing of existing pieces |
| KBs | SOURCE OF TRUTH — self-contained deep dives other components trust |

New logic goes to the layer that owns it — the `component-model` skill walks the decision; the SDD workflow components are the reference implementation.

**Current Status:** v3.2.0 shipped (Agent Router v2 Phase 1, Judge V0, `--judge` flag, local-first agent overrides). Linear is the project tracker (source of truth).

---

## Repository Structure

```text
agentspec/
├── .claude/                 # Claude Code integration
│   ├── agents/              # 58 specialized agents
│   │   ├── architect/       # 8 system-level design agents
│   │   ├── cloud/           # 10 AWS, GCP, cloud services, CI/CD
│   │   ├── platform/        # 6 Microsoft Fabric specialists
│   │   ├── python/          # 6 Python dev, code quality, prompts
│   │   ├── test/            # 3 testing, data quality, contracts
│   │   ├── data-engineering/ # 15 DE implementation specialists
│   │   ├── dev/             # 4 developer tools & productivity
│   │   └── workflow/        # 6 SDD phase agents
│   │
│   ├── commands/            # 31 slash commands
│   │   ├── workflow/        # SDD commands (7)
│   │   ├── data-engineering/ # DE commands (8)
│   │   ├── core/            # Utility commands (5)
│   │   ├── knowledge/       # KB commands (1)
│   │   ├── review/          # Review commands (2)
│   │   └── visual-explainer/ # Visual documentation commands (8)
│   │
│   ├── skills/              # 19 source skills: sdd-* phase skills + sdd-workflow umbrella,
│   │   │                    #   GitHub trio (github-cr-adr/-issue, github-post-issue),
│   │   │                    #   authoring (component-model, create-skill*, create-agent*),
│   │   │                    #   kb-build, visuals (visual-explainer, excalidraw-diagram),
│   │   │                    #   agent-router, team comms (meeting-analysis*, standup-report*)
│   │   │                    #   (* = repo-local, excluded from the plugin; see docs/reference)
│   │
│   ├── sdd/                 # SDD framework
│   │   ├── architecture/    # WORKFLOW_CONTRACTS.yaml, ARCHITECTURE.md
│   │   ├── templates/       # 5 document templates (DE-aware)
│   │   ├── features/        # Active development
│   │   ├── reports/         # Build reports
│   │   └── archive/         # Shipped features
│   │
│   └── kb/                  # Knowledge Base (24 domains)
│       ├── _templates/      # 7 KB domain templates
│       ├── _index.yaml      # Domain registry
│       ├── shared/          # Cross-domain anti-patterns and conventions
│       ├── dbt/             # dbt patterns and concepts
│       ├── spark/           # PySpark, Spark SQL
│       ├── sql-patterns/    # SQL best practices
│       ├── airflow/         # DAG patterns
│       ├── streaming/       # Flink, Kafka, CDC
│       ├── data-modeling/   # Star schema, Data Vault, SCD
│       ├── data-quality/    # GE, Soda, observability
│       ├── lakehouse/       # Iceberg, Delta, catalogs
│       ├── cloud-platforms/ # Snowflake, Databricks, BigQuery
│       ├── ai-data-engineering/ # RAG, vector DBs, features
│       ├── modern-stack/    # DuckDB, Polars, SQLMesh
│       ├── aws/             # Lambda, S3, Glue, SAM
│       ├── gcp/             # Cloud Run, Pub/Sub, BigQuery
│       ├── microsoft-fabric/ # Lakehouse, Warehouse, Pipelines
│       ├── lakeflow/        # Databricks Lakeflow (DLT)
│       ├── medallion/       # Bronze/Silver/Gold architecture
│       ├── supabase/        # pgvector, RLS, Edge Functions, Auth
│       ├── prompt-engineering/ # Chain-of-thought, extraction
│       ├── genai/           # Multi-agent systems, guardrails
│       ├── pydantic/        # Validation, LLM output schemas
│       ├── python/          # Python patterns and idioms
│       ├── testing/         # pytest, fixtures, CI testing
│       └── terraform/       # IaC modules, state, workspaces
│
├── docs/                    # Documentation
│   ├── getting-started/     # Installation and first pipeline
│   ├── concepts/            # SDD pillars through DE lens
│   ├── tutorials/           # dbt, star schema, Spark, streaming tutorials
│   └── reference/           # Full catalog: agents, commands, KB domains
│
├── plugin/                  # Generated plugin (built by build-plugin.sh)
│   ├── .claude-plugin/      # Plugin manifest + marketplace config
│   ├── agents/              # Copied + path-rewritten agents
│   ├── commands/            # Copied + path-rewritten commands
│   ├── skills/              # 16 skills (15 from .claude/ + 1 plugin-only; repo-local excluded)
│   ├── kb/                  # Copied KB domains
│   ├── sdd/                 # Templates + architecture (no features/reports/archive)
│   ├── hooks/               # SessionStart workspace init
│   └── scripts/             # init-workspace.sh
│
├── plugin-extras/           # Plugin-only content (merged into plugin/ by build)
│   ├── skills/              # data-engineering-guide
│   ├── hooks/               # hooks.json
│   └── scripts/             # init-workspace.sh
│
├── Makefile                 # Developer entry point — `make help` lists all targets
├── build-plugin.sh          # Builds plugin/ from .claude/ (invokes scripts/generate-agent-router.py)
├── scripts/                 # Build tooling (not shipped in plugin)
│   ├── generate-agent-router.py  # Regenerates agent-router SKILL.md + routing.json from agent frontmatter
│   └── judge.py             # Judge V0: OpenRouter second opinion (backend for /judge command)
├── tests/                   # pytest suite (27 tests) — `make test`
├── .shellcheckrc            # Lint config for shell scripts
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # Contribution guide
├── SECURITY.md              # Security policy
└── README.md                # Project overview
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

Data engineering example:

```bash
# Design a star schema
/schema "Star schema for e-commerce analytics"

# Scaffold a pipeline
/pipeline "Daily orders ETL from Postgres to Snowflake"

# Generate quality checks
/data-quality models/staging/stg_orders.sql
```

---

## Active Development Tasks

| Task | Status | Description |
|------|--------|-------------|
| Data engineering pivot | Done | 24 KB domains, 58 agents (8 categories), 31 commands |
| Adapt existing agents for DE | Done | code-reviewer, code-cleaner, test-generator, design, define, build |
| Adapt SDD templates for DE | Done | BRAINSTORM, DEFINE, DESIGN, BUILD_REPORT templates |
| Documentation overhaul | Done | Getting started, concepts, tutorials, reference, README |
| Create CLAUDE.md.template | Pending | Template for user projects |
| Judge Layer V0 (`/judge`) | Done | OpenRouter cross-model second opinion with budget ledger |
| `--judge` flag on phase commands | Done | Inline cross-model verification on `/define`, `/design`, `/build` |
| Judge Layer V1+ | Planned | Multi-model ensemble, PostToolUse hook, automated escalation |
| Flag System (progressive enhancement) | Planned | Unified flag vocabulary across phase commands |
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
- `kb_domains` field for DE agents

### KB Domains

- `index.md` - Domain overview
- `quick-reference.md` - Cheat sheet
- `concepts/` - 3-6 concept files
- `patterns/` - 3-6 pattern files with code examples

---

## Commands Available

### SDD Workflow (7)

| Command | Purpose |
|---------|---------|
| `/brainstorm` | Explore ideas (Phase 0) |
| `/define` | Capture requirements (Phase 1) |
| `/design` | Create architecture (Phase 2) |
| `/build` | Execute implementation (Phase 3) |
| `/ship` | Archive completed work (Phase 4) |
| `/iterate` | Update existing docs (Cross-phase) |
| `/create-pr` | Create pull request |

### Data Engineering (8)

| Command | Purpose |
|---------|---------|
| `/pipeline` | DAG/pipeline scaffolding |
| `/schema` | Interactive schema design |
| `/data-quality` | Quality rules generation |
| `/lakehouse` | Table format + catalog guidance |
| `/sql-review` | SQL-specific code review |
| `/ai-pipeline` | RAG/embedding scaffolding |
| `/data-contract` | Contract authoring (ODCS) |
| `/migrate` | Legacy ETL migration |

### Core & Utilities (8)

| Command | Purpose |
|---------|---------|
| `/status` | Project status report |
| `/create-kb` | Create KB domain |
| `/review` | Dual-AI code review (CodeRabbit + Claude) |
| `/judge` | Cross-model second opinion via OpenRouter (V0) |
| `/meeting` | Meeting transcript analysis |
| `/memory` | Save session insights |
| `/sync-context` | Update CLAUDE.md |
| `/readme-maker` | Generate README |

### Visual Explainer (8)

| Command | Purpose |
|---------|---------|
| `/generate-web-diagram` | Standalone HTML diagram |
| `/generate-slides` | Magazine-quality slide deck as HTML |
| `/generate-visual-plan` | Visual implementation plan |
| `/diff-review` | Before/after architecture comparison |
| `/plan-review` | Current codebase vs. proposed plan |
| `/project-recap` | Project state and cognitive debt |
| `/fact-check` | Verify document accuracy against codebase |
| `/share` | Share HTML page via Vercel |

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Phase transition rules |
| `.claude/sdd/templates/*.md` | Document templates (DE-aware) |
| `.claude/kb/_templates/*.template` | KB domain templates |
| `.claude/kb/_index.yaml` | KB domain registry (24 domains) |
| `.claude/agents/README.md` | Agent routing + escalation map |
| `.claude/agents/architect/` | System-level design agents (schema, pipeline, lakehouse) |
| `.claude/agents/cloud/` | AWS, GCP, CI/CD, deployment agents |
| `.claude/agents/platform/` | Microsoft Fabric specialists |
| `.claude/agents/python/` | Python dev, code quality, prompt engineering |
| `.claude/agents/test/` | Testing, data quality, data contracts |
| `.claude/agents/dev/` | Prompt crafter, codebase explorer, shell scripts, meeting analyst |
| `.claude/skills/visual-explainer/` | HTML generation skill (templates, CSS patterns, scripts) |
| `.claude/skills/excalidraw-diagram/` | Excalidraw JSON generation skill |
| `.claude/skills/agent-router/` | Auto-generated routing rules (regenerated by `scripts/generate-agent-router.py`) |
| `.claude/skills/github-cr-adr/` · `github-cr-issue/` · `github-post-issue/` | GitHub workflow trio: draft ADRs/issues → guarded publish + curation (ephemeral drafts in `.claude/sdd/drafts/`) |
| `.claude/skills/component-model/` + `.claude/kb/shared/component-model.md` | The layer-decision skill + the canonical component model it operationalizes |
| `.claude/skills/create-skill/` · `create-agent/` · `kb-build/` | Authoring SOPs: new skills and agents (repo-local; create-skill defers to upstream `skill-creator`), high-assurance KB domains |
| `.claude/skills/sdd-*/` | Per-phase SDD methodology (brainstorm, define, design, build, ship, iterate) — loaded by the thin phase agents and commands; `sdd-workflow` is the umbrella |
| `.claude/skills/meeting-analysis/` · `standup-report/` | Team communication: transcript analysis, daily standup (repo-local — excluded from the distributed plugin via `REPO_LOCAL_SKILLS` in `build-plugin.sh`) |

---

## Version

- **Version:** 3.2.0
- **Status:** Release
- **Last Updated:** 2026-05-19
