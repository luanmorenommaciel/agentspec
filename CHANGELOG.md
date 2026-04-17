# Changelog

All notable changes to AgentSpec will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [3.1.0] - 2026-04-17

### Added

- **New skill: `agent-router`** — intelligent routing table that maps file patterns, intent keywords, and domain context to all 58 agents. Includes model cost optimization strategy (Haiku 70% / Sonnet 20% / Opus 10%) and serial/parallel composition hints
- **New command: `/status`** — comprehensive project status report scanning SDD workspace, git state, codebase health (tests, TODOs, docs), and generating actionable recommendations with suggested next commands
- **Stack auto-detection in `init-workspace.sh`** — SessionStart hook now detects 10+ technology stacks (dbt, Lakeflow, Lambda, Airflow, Supabase, Terraform, Spark, Streaming, Fabric, Data Quality) and generates `.detected-stack.md` with recommended KB domains, agents, and commands
- **New KB domain: `supabase/`** — dedicated knowledge base with 4 concepts (pgvector-fundamentals, rls-policies, edge-functions, realtime) and 3 patterns (rag-vector-store, multi-tenant-rls, webhook-edge-function)
- New KB concepts for `lakeflow/`: expectations-model, cdc-fundamentals, deployment-model (now 5 concepts, within 3-6 spec)
- New KB file: `aws/quick-reference.md` — consolidated Lambda + Deployment cheat sheet
- New file: `commands/visual-explainer/README.md` — documents all 8 visual-explainer commands
- Plugin-only skills (`sdd-workflow`, `data-engineering-guide`) documented in `docs/reference/README.md`
- Vercel CLI prerequisite note in `/share` command

### Fixed

- **Critical:** 4 agents referenced non-existent KB domains in body text — `supabase-specialist` (supabase/), `qdrant-specialist` (qdrant/, n8n/), `ci-cd-specialist` (devops/), `ai-prompt-specialist-gcp` (gemini/, langfuse/) — all remapped to existing domains
- **Critical:** `lakeflow-expert` dead reference to `08-operations/limitations.md` → corrected to `reference/limitations.md`
- Dead `README.md` reference in `excalidraw-diagram/SKILL.md` — replaced with inline setup pointer
- Dead `./commands/` references in `visual-explainer/SKILL.md` — corrected to `.claude/commands/visual-explainer/`
- Malformed `mcp_servers` frontmatter in `llm-specialist.md` — reformatted to proper YAML objects with `tools:` field
- Missing `tools:` field in `mcp_servers` for 3 lakeflow T3 agents (lakeflow-architect, lakeflow-pipeline-builder, lakeflow-expert)
- `spark-specialist` → `spark-engineer` in `docs/concepts/README.md` build delegation
- Code of Conduct entry in CHANGELOG v1.0.0 clarified as "referenced in CONTRIBUTING.md"
- `/share` command added to README Visual & Utilities table

### Changed

- Command count: 29 → 30 (added `/status`)
- Skill count: 3 in source / 5 in plugin (added `agent-router` to source; plugin adds `sdd-workflow`, `data-engineering-guide`)
- KB domain count: 22 → 23 (added `supabase/`) — updated across all docs, SDD files, agents README, CLAUDE.md, README.md, and WORKFLOW_CONTRACTS.yaml
- `WORKFLOW_CONTRACTS.yaml` version bumped from 2.1.0 → 3.0.0
- `_index.yaml` version bumped to 2.2, supabase domain registered
- `supabase-specialist` agent now uses dedicated `supabase/` KB domain instead of `ai-data-engineering/` (semantically correct)
- Skills section in `docs/reference/README.md` updated to "2 core + 2 plugin-only" with plugin-only skills documented
- Plugin rebuilt — 58 agents, 30 commands, 5 skills, 23 KB domains

## [3.0.0] - 2026-03-29

### Added

- **Claude Code Plugin support**: AgentSpec is now distributable as a proper Claude Code plugin
- Plugin manifest (`plugin/.claude-plugin/plugin.json`) with marketplace metadata
- `build-plugin.sh` — build script that packages `.claude/` into plugin format with path rewriting
- `plugin-extras/` — plugin-only skills, hooks, and scripts not in `.claude/`
- New skill: `sdd-workflow` — auto-invoked when users discuss feature development workflow
- New skill: `data-engineering-guide` — auto-invoked when users discuss data engineering tasks
- `hooks/hooks.json` — SessionStart hook for workspace initialization
- `scripts/init-workspace.sh` — idempotent workspace directory creator
- Marketplace configuration for self-hosted distribution
- Plugin installation method in README alongside legacy `cp -r` method

### Changed

- All internal paths in plugin output rewritten from `.claude/` to `${CLAUDE_PLUGIN_ROOT}/`
- Skills count increased from 2 to 4 (added sdd-workflow, data-engineering-guide)
- Version bumped to 3.0.0 (new distribution model)

### Architecture

- `.claude/` remains the source of truth for development
- `build-plugin.sh` generates `plugin/` directory with proper plugin structure
- Plugin-only content lives in `plugin-extras/` to survive build clean cycles
- Workspace-specific paths (features/, reports/, archive/) preserved as project-relative

## [2.1.1] - 2026-03-29

### Added

- Documentation for 8 visual-explainer commands (`/generate-web-diagram`, `/generate-slides`, `/generate-visual-plan`, `/diff-review`, `/plan-review`, `/project-recap`, `/fact-check`, `/share`)
- Documentation for skills system (2 skills: `visual-explainer`, `excalidraw-diagram`)
- Skills contribution guide in CONTRIBUTING.md

### Fixed

- Command count corrected from 21 to 29 across all documentation (CLAUDE.md, README, commands/README, docs/reference)
- Fixed `meeting-analyst` incorrectly listed in Architect category (belongs in Dev) in sdd/README.md and README.md; replaced with `kb-architect`
- Fixed "23 KB domains" typo in sdd/README.md version history (correct: 22)
- Removed orphan `lakeflow/_index.yaml` (only domain with its own index file; master `_index.yaml` already covers it)

## [2.1.0] - 2026-03-26

### Added

- Multi-cloud agent coverage: 58 agents across 8 categories (was 27 across 5)
- New agent categories: architect/ (8), cloud/ (10), platform/ (6), python/ (6), test/ (3), dev/ (4)
- 11 additional KB domains: aws, gcp, microsoft-fabric, lakeflow, medallion, prompt-engineering, genai, pydantic, python, testing, terraform
- Supabase, Qdrant, and Lambda specialist agents
- Spark ecosystem agents: spark-specialist, spark-streaming-architect, spark-performance-analyzer
- Lakeflow ecosystem agents: lakeflow-architect, lakeflow-expert, lakeflow-pipeline-builder
- Shell script specialist and CI/CD specialist agents

### Changed

- Reorganized 15 agent folders into 8 clean semantic categories
- Eliminated duplicate agents (fabric-architect, fabric-pipeline-developer had inferior copies)
- Dissolved legacy categories: ai-ml/, code-quality/, communication/, exploration/, database/, ci-cd/
- Complete documentation overhaul: all docs pages rewritten for v2.1 accuracy
- SDD README, _index.md, ARCHITECTURE.md, WORKFLOW_CONTRACTS.yaml bumped to v2.1.0
- All root files (README, CLAUDE.md, CONTRIBUTING, SECURITY) aligned with actual counts

### Removed

- `/dev` command (file deleted; prompt-crafter agent still available directly)
- overnight-builder agent (superseded by prompt-crafter)
- adaptive-explainer and linear-project-manager agents
- PLAN_DATA_ENGINEERING_PIVOT.md from features/ (pivot complete)
- tasks/backlog.md and empty tasks/ directory

## [2.0.0] - 2026-03-26

### Added

- Data engineering specialization across the entire framework
- 11 new KB domains: dbt, spark, sql-patterns, airflow, streaming, data-modeling, data-quality, lakehouse, cloud-platforms, ai-data-engineering, modern-stack
- 11 new data engineering agents: dbt-specialist, spark-engineer, pipeline-architect, schema-designer, sql-optimizer, streaming-engineer, lakehouse-architect, data-quality-analyst, ai-data-engineer, data-platform-engineer, data-contracts-engineer
- 8 new data engineering commands: /pipeline, /schema, /data-quality, /lakehouse, /sql-review, /ai-pipeline, /data-contract, /migrate
- Data contract support in DEFINE phase (schema, SLAs, lineage)
- Pipeline architecture section in DESIGN phase (DAG, partitions, incremental strategy)
- Data engineering quality gates in BUILD phase (dbt build, sqlfluff, GE suites)
- DE delegation map in WORKFLOW_CONTRACTS.yaml

### Changed

- SDD templates extended with data engineering sections
- Existing agents (code-reviewer, code-cleaner, test-generator, design, define, build) adapted for DE
- All documentation rewritten with data engineering examples
- README, CLAUDE.md, CONTRIBUTING rebranded for data engineering focus

## [1.1.0] - 2026-02-24

### Added

- Complete documentation overhaul: getting-started, concepts, tutorials, reference guides
- Linear as project source of truth (60 issues, 6 milestones, 9 project documents)

### Changed

- KB domains cleaned — removed project-specific domains, kept framework scaffolding
- Agent prompts sanitized — removed all project-specific references
- `concept.md.template` section renamed from "The Pattern" to "The Concept"
- `test-case.json.template` now documents valid type values
- CLAUDE.md updated with current project status and active tasks
- README, CONTRIBUTING, SECURITY, CHANGELOG rewritten for public release

### Removed

- Project-specific KB domains (agentspec, projects)
- `design/agent-spec-plan-todo-list.md` (migrated to Linear)

### Fixed

- All 60 Linear issues linked to correct milestones
- Duplicate Linear documents consolidated (4 deprecated with redirects)

## [1.0.0] - 2026-02-03

### Initial Release

- Initial release of AgentSpec
- 5-phase SDD workflow (Brainstorm, Define, Design, Build, Ship)
- 16 specialized agents
  - 6 workflow agents (brainstorm, define, design, build, ship, iterate)
  - 4 code-quality agents (reviewer, cleaner, documenter, test-generator)
  - 4 communication agents (adaptive-explainer, linear-project-manager, meeting-analyst, the-planner)
  - 2 exploration agents (codebase-explorer, kb-architect)
- 12 slash commands
- Knowledge Base (KB) framework with 7 templates
- SDD document templates (5 phases)
- Workflow contracts (YAML-based phase transitions)

### Documentation

- README with quick start guide
- CONTRIBUTING guidelines
- Code of Conduct (referenced in CONTRIBUTING.md)
- Agent reference documentation
- KB framework guide
