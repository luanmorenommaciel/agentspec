---
name: status
description: Generate a comprehensive project status report — active features, recent decisions, agent recommendations, and health assessment
---

# Status Report Command

Generates a project status report by scanning the SDD workspace, git history, and codebase health indicators.

## Usage

```bash
/status                    # Full project status report
/status "sprint review"    # Status with specific context for a sprint review
```

---

## What It Does

1. **Scans** the SDD workspace for active and recently shipped features
2. **Checks** git state for recent commits, branches, and uncommitted work
3. **Detects** project health (tests, TODOs, documentation, stack)
4. **Generates** actionable recommendations based on current state

---

## Execution Process

Execute all steps inline (no agent delegation) and produce the report directly.

### Step 1: Scan SDD Workspace

```text
# Active features
Glob(".claude/sdd/features/BRAINSTORM_*.md")
Glob(".claude/sdd/features/DEFINE_*.md")
Glob(".claude/sdd/features/DESIGN_*.md")

# Build reports
Glob(".claude/sdd/reports/BUILD_REPORT_*.md")

# Recently shipped
Glob(".claude/sdd/archive/*")
```

For each discovered document:
- Extract the feature name from the filename
- Read the first 10 lines to determine status and last updated date
- Determine the current SDD phase (Brainstorm, Define, Design, Build, Shipped)
- Flag any blockers mentioned in the document

### Step 2: Check Git State

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git status --short

# Current branch
git branch --show-current

# All local branches
git branch

# Check for pending PRs (only if gh CLI is available)
gh pr list --state open --limit 5 2>/dev/null || echo "gh CLI not available"
```

### Step 3: Detect Project Health

```text
# Test files
Glob("**/test_*.py")
Glob("**/*_test.py")
Glob("**/*.test.ts")
Glob("**/*.test.js")
Glob("**/*.spec.ts")
Glob("**/*.spec.js")
Glob("**/tests/**/*.py")

# TODO/FIXME count
Grep("TODO|FIXME", output_mode="count")

# Documentation check
Glob("CLAUDE.md")
Glob("README.md")

# Stack detection via config files
Glob("**/pyproject.toml")
Glob("**/package.json")
Glob("**/dbt_project.yml")
Glob("**/Dockerfile")
Glob("**/*.tf")
Glob("**/airflow.cfg")
Glob("**/requirements.txt")
Glob("**/Cargo.toml")
Glob("**/go.mod")
Glob("**/pom.xml")

# KB domain alignment
Glob(".claude/kb/*/index.md")
```

Compare detected technologies against available KB domains and note any gaps.

### Step 4: Generate Recommendations

Based on the collected data, produce recommendations:

- **Next SDD phase**: If a feature is in Define, recommend `/design`. If in Design, recommend `/build`. If nothing is active, recommend `/brainstorm` or `/define`.
- **Agent recommendations**: Based on detected work (e.g., SQL files suggest sql-optimizer, dbt files suggest dbt-specialist, Python files suggest code-reviewer).
- **Health fixes**: Flag stale branches (branches other than main with no recent commits), failing tests, missing documentation, high TODO counts, or uncommitted changes.

---

## Output Format

Generate the report in this exact structure:

```markdown
# Project Status Report

**Project:** {project name from package.json, pyproject.toml, dbt_project.yml, or directory name}
**Branch:** {current branch}
**Date:** {today's date}

---

## Active Work

| Feature | Phase | Status | Last Updated |
|---------|-------|--------|--------------|
| {feature_name} | {Brainstorm/Define/Design/Build} | {In Progress/Blocked/Ready for next phase} | {date from file} |

> {If no active features: "No active SDD features. Use `/brainstorm` or `/define` to start."}

## Recently Shipped

| Feature | Shipped Date |
|---------|-------------|
| {feature_name} | {date} |

> {If no shipped features: "No recently shipped features found in archive."}

## Recent Activity

| Commit | Message |
|--------|---------|
| {short hash} | {message} |

**Uncommitted changes:** {count} files
**Open PRs:** {count or "N/A"}

## Project Health

| Check | Status | Details |
|-------|--------|---------|
| Tests | {Pass/Fail/None} | {count} test files found |
| Documentation | {CLAUDE.md exists/missing}, {README.md exists/missing} | |
| Uncommitted changes | {Clean/N files changed} | {list files if < 10} |
| TODOs/FIXMEs | {count} found | Review with `Grep("TODO\|FIXME")` |
| Stack detection | {Detected} | {list: Python, dbt, Docker, Terraform, etc.} |
| KB coverage | {Covered/Gaps} | {list any detected tech without matching KB domain} |

## Recommendations

1. **Next step:** {What to do next based on active work state}
2. **Agent to use:** {Which agent would help most right now and why}
3. **Health action:** {Most important health issue to address, if any}

## Suggested Commands

| Command | Reason |
|---------|--------|
| `/{command}` | {Why this command is relevant right now} |
| `/{command}` | {Why this command is relevant right now} |
```

---

## Example

```text
User: /status

Scanning SDD workspace...
  Found 2 active features, 1 shipped
Checking git state...
  Branch: feat/judge-layer, 3 uncommitted files
Detecting project health...
  47 test files, CLAUDE.md present, 12 TODOs

# Project Status Report

**Project:** agentspec
**Branch:** feat/judge-layer
**Date:** 2026-04-14

---

## Active Work

| Feature | Phase | Status | Last Updated |
|---------|-------|--------|--------------|
| JUDGE_LAYER | Design | In Progress | 2026-04-12 |
| TELEMETRY | Define | Ready for next phase | 2026-04-10 |

## Recently Shipped

| Feature | Shipped Date |
|---------|-------------|
| PLUGIN_DISTRIBUTION | 2026-03-29 |

## Recent Activity

| Commit | Message |
|--------|---------|
| 3b1ada5 | fix: update banner command count 21 to 29 |
| 68c6b92 | feat: redesign README and update banner stats |

**Uncommitted changes:** 3 files
**Open PRs:** 1

## Project Health

| Check | Status | Details |
|-------|--------|---------|
| Tests | None | 0 test files found |
| Documentation | Present | CLAUDE.md and README.md both exist |
| Uncommitted changes | 3 files | SECURITY.md, meeting-analyst.md, share.md |
| TODOs/FIXMEs | 12 found | Scan with Grep for details |
| Stack detection | Detected | Markdown, Shell, Python |
| KB coverage | Covered | 24 KB domains available |

## Recommendations

1. **Next step:** JUDGE_LAYER is in Design phase — run `/build JUDGE_LAYER` when design is finalized
2. **Agent to use:** design-agent for completing the JUDGE_LAYER design
3. **Health action:** Commit or stash the 3 uncommitted files to keep the branch clean

## Suggested Commands

| Command | Reason |
|---------|--------|
| `/build JUDGE_LAYER` | Design phase is complete, ready to build |
| `/design TELEMETRY` | TELEMETRY has a DEFINE doc, ready for design |
| `/sync-context` | Keep CLAUDE.md in sync after recent changes |
```

---

## Best Practices

### When to Run

- At the start of a new session to regain context
- Before sprint reviews or standups
- After returning from a break
- When onboarding to an unfamiliar project

### Performance

This command runs inline without agent delegation. It uses only Glob, Grep, Read, and Bash tools. Typical execution time is under 30 seconds.
