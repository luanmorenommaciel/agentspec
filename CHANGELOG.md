# Changelog

All notable changes to AgentSpec will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- **`--judge` flag on `/define`, `/design`, `/build`** — progressive-enhancement integration of Judge V0 into the SDD workflow:
  - `/define FEATURE --judge` → cross-model spec-quality review (default: openai/gpt-4o)
  - `/design FEATURE --judge` → architectural-soundness review (default: openai/gpt-4o)
  - `/build FEATURE --judge` → BUILD_REPORT correctness review (default: openai/gpt-4o; consider openai/codex-mini for pure-code builds)
  - Three modes per command: advisory (`--judge`), gated (`--judge=strict`), model-override (`--judge=MODEL` or `--judge=strict:MODEL`)
  - Phase-aware system prompts in `scripts/judge.py` tuned to each artifact type (DEFINE for requirements, DESIGN for architecture, BUILD for code)
  - Defaults preserved — running the commands without `--judge` behaves identically to v3.1.0
  - Budget exhaustion, config errors, and network errors never block the phase — judge failures degrade to "as if `--judge` was not passed"
- **Stale-count syncs** (from Audit 3): CLAUDE.md, commands/README.md, docs/reference/README.md, and root README.md now consistently reflect 58 agents / 31 commands / 3 skills / 23 KB domains / v3.1.0 current status
- `/status` added to Core Commands table in `.claude/commands/README.md` (was missing since v3.1.0)
- `/judge` added to Review Commands table in `.claude/commands/README.md`
- **`Makefile`** as the primary contributor entry point — one-line access to build, test, check, lint, generate, clean. `make help` lists all targets with descriptions.
- **`.shellcheckrc`** at repo root — `shell=bash`, disables SC1091/SC2155 (noisy for our repo). Used by both local `make lint` and CI.
- **`.github/workflows/quality-checks.yml`** — new GitHub Actions workflow split into two jobs:
  - `python`: pytest suite + `generate-agent-router.py --check` drift guard
  - `shellcheck`: shellcheck -S warning on all three first-party shell scripts
- **`init-workspace.sh` mandatory header block** (audit-tier-3): shebang, Prerequisites, Usage sections, `--help` flag
- **Agent Router v2 — Phase 1 (Build-Time Generation)** — the `agent-router` skill is now auto-generated from agent frontmatter, eliminating hand-maintained routing tables:
  - `scripts/generate-agent-router.py` — parses frontmatter across all 58 agents and derives category/tier/model/kb_domains/escalations without any new frontmatter fields required
  - Generates both `.claude/skills/agent-router/SKILL.md` (human-readable) and `.claude/skills/agent-router/routing.json` (machine-readable, foundation for future semantic layer)
  - `--check` mode for CI: fails with a unified diff if on-disk output drifts from generated content
  - Content hash stamped in SKILL.md (currently `d2970b1b988f`) for drift detection
  - `DO NOT EDIT` header pointing contributors back to the script
- `scripts/` directory at repo root for build tooling (distinct from `plugin-extras/scripts/` which ships in the plugin)
- **Judge Layer V0** — opt-in cross-model second opinion via OpenRouter:
  - New `/judge <file>` slash command at `.claude/commands/review/judge.md`
  - `scripts/judge.py` — calls OpenRouter's OpenAI-compatible API with zero SDK dependencies (pure stdlib `urllib`)
  - Default model `openai/gpt-4o-mini`; overridable via `JUDGE_MODEL` env or `--model` flag
  - Hard per-day budget ceiling (default 10 calls, overridable via `JUDGE_BUDGET`) enforced by append-only ledger at `.claude/storage/judge-ledger.jsonl`
  - Structured JSON verdict rendered as markdown: PASS/FAIL, confidence 0-1, severity-ranked concerns with evidence citations, suggested fixes
  - Distinct exit codes (0 PASS, 1 FAIL, 2 config, 3 budget, 4 API) for future CI/shell composition
  - `/judge --ledger` shows today's usage
  - Setup guide at `docs/getting-started/judge-setup.md` covering OpenRouter key, cost reference, privacy, troubleshooting
  - No MCP server, no auto-triggering hook, no classifier in V0 — user opts in per invocation
- **Flag System (Progressive Enhancement Framework)** added to backlog as 🔵 P1 for v3.2 — unified flag vocabulary across all phase commands, preserving AgentSpec's simple surface while enabling opt-in depth

### Changed

- `build-plugin.sh` gained **Step 0** — runs the agent-router generator before copying artifacts into `plugin/`, ensuring the plugin ships the current routing tables
- `CLAUDE.md` repository tree updated to reflect the new `scripts/` directory
- `tasks/backlog.md` marks Agent Router v2 Phase 1 as 🟢 shipped and tracks Phases 2-4 as future work

### Fixed

- Broken link in `.claude/commands/README.md`: `[data-engineering/README.md](data-engineering/README.md)` → `[data-engineering/](data-engineering/)` (referenced file didn't exist; directory does)

### Philosophy

Adding, renaming, or retiring an agent no longer requires editing the router. Edit the agent's frontmatter → run `./build-plugin.sh` (or the generator standalone) → routing updates itself.

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
