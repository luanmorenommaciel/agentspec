---
name: kb-build
description: |
  Build a high-assurance, source-verified knowledge base where every claim is source-cited and adversarially fact-checked before it lands.
  Grounds in the repo's KB house style, plans the domain, researches with an independent refutation pass, builds with kb-architect subagents, runs an independent fact-check gate, and registers the domain additively in the KB index.
  Use when the user wants a validated or foundational KB where every claim must be source-cited and fact-checked — "build a KB", "create a knowledge base", "validated KB", "high-assurance KB" — or when encoding researched knowledge into a reusable domain many agents will trust.
  For a quick single-pass KB, use the create-kb command instead.
---

# KB Build — high-assurance, source-verified KB creation

Build a knowledge base where every claim is source-cited and adversarially verified before it lands.
This skill serves two purposes: it produces the KB, and its body documents the process — read it as the SOP for how validated knowledge enters the repository.

A KB is a component whose single responsibility is to be a faithful knowledge-bearer.
A foundational KB is consulted by many agents, so one unverified "standard" propagates into all of them.
Faithfulness is therefore non-negotiable, and the verification bar is intrinsic to the kind of claim — a notation or standard claim demands an authoritative source — regardless of how many readers the KB will have.
The distilled reasoning lives in `references/lessons.md`.

## When to use vs the create-kb command

The `create-kb` command is the lighter sibling: a direct, single-pass `kb-architect` run relying on the agent's own validation. Pick by stakes:

| Use `kb-build` (this skill) | Use the `create-kb` command |
|---|---|
| Foundational or high-stakes domain | Quick, low-stakes domain |
| Every claim cited and independently fact-checked | kb-architect's own validation suffices |
| Research + adversarial verification + fact-check gate | Single pass, no separate verification layer |
| Worth more tokens for assurance | Token-light |

## Scope fence

KBs hold technical domain knowledge for grounding agents: concepts, patterns, specs, quick references. Two things never belong in a KB:

- **Architecture decisions** — record them as ADRs in the repository's decision log; the KB may cite a decision, never host it.
- **Meeting notes** — they belong in the project's notes; distill any durable technical knowledge out of them (with sources) before it enters a KB.

## Process

Run the six stages in order. Each stage has an output and a gate; do not start the next stage until the gate passes. Two operating principles apply throughout:

- Delegate heavy stages (research, verification, authoring) to subagents; keep the main context for orchestration and gate decisions.
- Persist intermediate outputs to files (plan, research notes, verification record) so later stages cite artifacts, not memory.

### Stage 1 — Ground

Read the house style before writing a single word:

1. Read every template in `${CLAUDE_PLUGIN_ROOT}/kb/_templates/`.
2. Read `${CLAUDE_PLUGIN_ROOT}/kb/_index.yaml`: the registry format, the file-size limits (the single source of truth for line budgets), and the shape of a domain entry.
3. Read one or two existing domains under `${CLAUDE_PLUGIN_ROOT}/kb/` end to end to see how concepts, patterns, specs, and entry points are actually written in this repository.

Then write an intent brief:

- **Audience:** which agents and humans will consult this KB, and with what intent (look up a value, pick an option, follow a procedure). Design for reader-type and reader-intent — never for reader count.
- **Scope:** what is in, and what is explicitly out.
- **Source material:** the candidate primary sources (official docs, standards bodies, source repositories), ranked.

**Output:** intent brief + ranked source list + the house-style constraints the build must obey.
**Gate:** you can state, in one sentence each, what the KB is for, who reads it, and which sources anchor it.

### Stage 2 — Plan

Delegate planning to the `the-planner` agent, passing the intent brief and the house-style constraints.
If the agent is unavailable in this installation, produce the same plan inline before proceeding — never skip the plan.

The plan must contain:

- **Research buckets:** the topic clusters to investigate, each naming its primary sources.
- **KB schema:** the target file list, mirroring the house precedent and the template line limits, for example:

  ```
  ${CLAUDE_PLUGIN_ROOT}/kb/<domain>/
    index.md               # entry point — orientation + file map
    quick-reference.md     # fast lookups
    concepts/<topic>.md    # one concept per file
    patterns/<topic>.md    # applied how-tos
    specs/<topic>.yaml     # machine-readable contracts
  ```

- **Source-priority list:** which source wins when two disagree (authoritative > secondary > community).
- **Build gate:** what must be verified before any KB file is written.

**Output:** the written plan.
**Gate:** every planned file maps to a template, and every research bucket names at least one primary source.

### Stage 3 — Research with adversarial verification

Research fills the plan's buckets; verification tries to tear the findings down.

1. **Gather.** Investigate each bucket. Where a workflow or orchestration harness is available, fan buckets out to parallel subagents; otherwise run them sequentially. Record every claim as: claim + source (URL or document id) + tier (authoritative > secondary > community).
2. **Deepen.** Follow up on the gaps and contradictions the first pass exposed.
3. **Verify adversarially.** A separate agent — or at minimum a separate fresh-context pass — independently re-fetches the primary source for each load-bearing claim and tries to refute it. Gatherers are incentivized to find; verifiers must be incentivized to refute.
4. **Synthesize.** Merge the verified claims into research notes under a working directory (for example `<research-notes-dir>/`), keeping the source and tier attached to each claim.

Rules of evidence:

- Current documentation beats training data. Check every version-sensitive or standard claim against live sources — via the docs MCP or web fetch available in the session — and never let model memory be the only citation.
- Community-only or unverifiable claims are demoted: they may appear as clearly labeled practitioner opinion, never as standards in concept or spec files.

**Output:** verified, source-cited research notes.
**Gate:** every load-bearing claim survived an independent refutation attempt, or was demoted and flagged.

### Stage 4 — Build

Author the KB from the verified research notes — never from memory.

- **Parallel path (when a workflow/orchestration harness exists):** author content files (concepts, patterns, specs, reference material) in parallel, launching each author as a `kb-architect`-type subagent so it carries the KB protocol — templates, line limits, validation headers, scoring.
- **Sequential fallback (no harness):** run the same authoring steps one at a time with individual subagent calls — one `kb-architect` invocation per file or file group. The order changes; the protocol and the gates do not.
- **If the `kb-architect` agent is unavailable:** brief a general-purpose subagent with the templates and the limits from `_index.yaml` — the protocol travels in the prompt.

After the content files, run a **synthesis pass** in a single context that sees the whole domain:

- Author the cross-cutting files — the domain `index.md`, `quick-reference.md`, and the domain manifest — since they need a view of the whole.
- Reconcile cross-links and shared vocabulary, both across the new files and with existing domains.

Sizing guidance:

- For a small KB (roughly five content files or fewer), a single `kb-architect` pass is simpler and sidesteps parallel-calibration risk.
- Parallelize when the file count or the assurance bar justifies it.
- Either way, Stage 5 is mandatory.

**Output:** the complete domain under `${CLAUDE_PLUGIN_ROOT}/kb/<domain>/`.
**Gate:** every file matches its template and line budget, and every factual statement traces to the research notes.

### Stage 5 — Independent fact-check gate

Before accepting the content, run an independent verification pass — fresh context, not one of the authors:

- Re-check the authored facts, values, and labels against their cited sources. This gate checks content correctness, not structure.
- Treat it as non-negotiable after a parallel build: parallel per-file authors can stamp "verified" on an incorrect detail that structural reconciliation will not catch. An independent judge catches what self-consistency misses.
- Correct any failing claim against its primary source, or demote and flag it. Never ship a wrong "verified" label.

**Output:** a pass/fail record per checked claim, plus the corrected files.
**Gate:** zero known-wrong claims; every unresolved doubt is flagged in the file, not silently kept.

### Stage 6 — Register the domain

Update the aggregator `${CLAUDE_PLUGIN_ROOT}/kb/_index.yaml` **additively**:

- Append the new domain entry following the registry's existing entry shape (name, description, path, entry points, and per-file metadata where the format uses it).
- Never rewrite, reorder, or "clean up" existing entries — the registry is shared state, and other domains' entries are not yours to touch.
- If you discover domain folders missing from the registry, record them (add an entry or note them for the maintainer) rather than dropping them silently.

**Output:** the updated registry.
**Gate:** the new domain resolves from `_index.yaml`, and a diff of the registry shows only additions.

## Tooling rules

- **Complementary, not exclusive.** Use a library-docs MCP (library and SDK documentation) and plain web fetch (standards bodies, official sites) together. Web fetch of the primary source is the reliable backbone: MCP reachability can vary across subagents, so never hard-depend on a single MCP, and keep a primary-source URL as the fallback for every MCP-sourced claim.
- **Primary sources anchor.** Official documentation, standards bodies, and source repositories anchor claims; secondary sources corroborate but never anchor a "standard".
- **OAuth-gated MCPs** may be unavailable in headless or subagent runs — confirm reachability before routing a verification step through one.

## Quality bar (non-negotiable)

- Faithfulness is intrinsic — never carry an unverified "standard", regardless of expected readership.
- A standard or notation claim requires an authoritative-tier source; both the adversarial pass (Stage 3) and the fact-check gate (Stage 5) apply to it.
- The KB is the single source of truth: consumers (skills, agents, commands) reference it, never restate it — two copies drift.
- Keep the repository's KB domains mutually consistent: shared vocabulary and cross-links, never forked definitions.
- Honesty over completeness: flag what could not be verified and label its tier, rather than fabricating certainty.

## References

- `references/lessons.md` — the nine distilled principles behind this SOP, each with its why. Read it before running this skill on a new domain, and re-read it when choosing between single-pass and parallel build or whenever skipping a verification step starts to look attractive.
- The `kb-architect` agent — the build protocol used as the subagent type in Stage 4.
- The `the-planner` agent — the planning delegate in Stage 2.
- The `create-kb` command — the lighter, single-pass sibling with no research or verification layer.
