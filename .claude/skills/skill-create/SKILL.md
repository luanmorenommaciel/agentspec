---
name: skill-create
description: |
  Repo-specific layer for adding a new Claude Code skill to this repository — naming
  conventions, where the skill lives (distributed, plugin-only, or repo-local), YAML
  frontmatter pitfalls, and the build/mirror/docs checklist a skill must pass before it
  ships in the plugin. For the general craft of writing skills (structure, descriptions,
  progressive disclosure, evals) it defers to the upstream skill-creator skill when that
  is installed. Use when the user wants to add a skill to this repository, turn a
  recurring workflow into a repo skill, or asks what conventions a new skill here must
  follow. Do not use for creating agents or knowledge bases — those have their own
  workflows — or for general skill-writing guidance outside this repository (use
  skill-creator directly).
---

# Create a Skill (repo conventions)

Author the skill itself with Anthropic's upstream `skill-creator` skill where it is installed — it owns the general methodology (structure, description writing, progressive disclosure, packaging, evals). This skill carries only what `skill-creator` cannot know: this repository's conventions and build pipeline. Do not duplicate the upstream methodology here or in the skills you write.

## Division of labor

| Concern | Owner |
|---|---|
| Skill structure, description craft, progressive disclosure, packaging, evals | `skill-creator` (upstream) — invoke it when available, fetch it when not |
| Naming, placement, frontmatter pitfalls, ship checklist | this skill |

When `skill-creator` is not installed, fall back in order:

1. **Fetch the upstream methodology directly** — it is public. Retrieve `https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md` (web fetch or `curl`) and follow it as if the skill were installed; it references sibling files under the same directory that can be fetched the same way when needed.
2. **Offline as well?** Three principles carry most of its weight: one skill = one capability (split when triggers stop being related); the `description` is the entire trigger mechanism (what it does + when to use it + one "do not use for" boundary, third person, ≤1024 chars); keep SKILL.md under ~500 lines and push detail into `references/` (read on demand), `scripts/` (deterministic helpers), and `assets/` (files used in output).

## Repo conventions

1. **Naming.** Kebab-case, at least one hyphen, `name` field == folder name. Prefer domain-verb or domain-noun compounds (`kb-build`, `github-post-issue`, `meeting-analysis`). Avoid noise words (`helper`, `tool`, `utils`, a `-skill` suffix) and avoid `-er` agent-style names for skills — those read as agent roles.
2. **Placement.** Three tiers:
   - Distributed skill → `.claude/skills/<name>/`; the build mirrors it into `plugin/skills/`.
   - Plugin-only skill → `plugin-extras/skills/<name>/`; merged in at build, absent from `.claude/`.
   - Repo-local skill (for contributors of this repository, not distributed) → `.claude/skills/<name>/` plus an entry in the `REPO_LOCAL_SKILLS` exclusion list in `build-plugin.sh`.
3. **Frontmatter.** Only supported keys (`name`, `description`, optionally `license`, `allowed-tools`, `metadata`, `compatibility`). YAML traps that fail silently: a ` #` inside an unquoted value truncates it; a `: ` inside an unquoted value breaks parsing; write multi-line descriptions as a literal block (`|`). Never invent keys — there is no `triggers:` field; the description IS the trigger.
4. **Internal paths.** Reference `.claude/kb/...`, `.claude/skills/...`, `.claude/agents/...` normally — the build rewrites them to plugin paths. `.claude/sdd/` workspace paths (`drafts/`, `features/`, `reports/`, `archive/`) are preserved as-is by design.

## Ship checklist

Every new skill passes this before review:

| # | Check | How |
|---|---|---|
| 1 | Structure valid | name matches folder and `^[a-z0-9]+(-[a-z0-9]+)+$`; description ≤1024 chars with triggers and a negative boundary; every referenced supporting file exists |
| 2 | Mirror in sync | run `./build-plugin.sh`, then commit the regenerated `plugin/` tree together with the skill; verify locally with `git diff --exit-code plugin/ .claude-plugin/` after a fresh rebuild — CI rebuilds the plugin and validates the fresh tree, so a stale committed mirror is caught at the latest in review |
| 3 | Docs updated | CHANGELOG `[Unreleased]`; skill counts and catalogs in `CLAUDE.md`, `README.md`, `plugin/README.md`, `docs/README.md`, `docs/reference/README.md` |
| 4 | No template residue | if the skill renders `{{PLACEHOLDER}}` templates, grep output for `\{\{[A-Z_]+\}\}` — zero hits |
