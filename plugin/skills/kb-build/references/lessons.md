# Lessons & Decision Principles — KB building

> Distilled from prior high-assurance KB builds: principles with their *why*, not a transcript.
> Read before running `kb-build` on a new domain; re-read 4, 8, and 9 before choosing a build topology or skipping a verification step.

## 1. A KB is a component; faithfulness is its single responsibility

**Design the KB as a faithful, well-structured knowledge-bearer — the quality bar is intrinsic, never a function of audience size.** A reference book should not print a falsehood whether one person or a million read it. Shape structure by reader-type and reader-intent (a taxonomy as a decision tree when the intent is "pick one"; a machine-readable spec when the reader is an agent) — never by reader count.

## 2. Verify; do not assume — especially your own defaults

**Probe reachability and re-check inherited rules instead of taking defensive defaults that quietly cost quality.** The two recurring failure modes: declaring a tool or MCP unreachable without probing it, and carrying a predecessor artifact's rules forward unchecked — audits of inherited rule sets routinely find a majority stale.

## 3. Complementary tools, not exclusive

**Use a library-docs MCP and plain web fetch together — never hard-depend on a single MCP.** MCP reachability is non-uniform across subagents and headless runs; web fetch of the primary source is the reliable backbone, so every MCP-sourced claim needs a primary-source URL to fall back to.

## 4. An adversarial gate guards the KB

**Have a separate verifier independently re-fetch the primary source and try to refute each load-bearing claim.** Gatherers are incentivized to find, not to doubt: tier every claim (authoritative > secondary > community) and demote community-only or unverifiable claims out of concept and spec files — a claim that cannot be tied to an authoritative source never enters as a "standard".

## 5. Single source of truth — reference, do not restate

**Knowledge lives in the KB once; skills, agents, and commands point at it and never copy it.** Two copies drift. Across domains, cross-link shared terms instead of letting each domain define them differently — a library still curates one catalog so two books do not disagree on a definition, and agents will not reconcile that on their own.

## 6. Untrusted artifacts are reference-only until validated

**Community skills and templates can be strong seeds — salvage the methodology, but verify every technical claim against primary docs before adopting.** Well-regarded community artifacts have shipped stale tool limits and outdated platform facts presented as hard rules; keep the philosophy, discard what fails verification, and label opinion as opinion.

## 7. Output-token limits are a per-response cap, not a wall

**Build large artifacts incrementally — write section by section across multiple edits, persist to files, and return a pointer.** The "output limit" objection conflates a per-response generation cap with a hard blocker; a subagent can author a KB of any size by writing incrementally.

## 8. Honesty over completeness

**Flag what you could not verify and label its source tier, rather than fabricating certainty.** A KB that says "unverified, secondary source" where that is the truth is more trustworthy — and more useful to the agents grounding on it — than one that over-claims.

## 9. Parallel build raises the ceiling but risks calibration

**Parallelize authoring only with an independent fact-check gate in place — structural reconciliation will not catch a wrong-but-"verified" detail.** A controlled comparison (same verified research, single-context build vs parallel instances plus a consistency pass, blind-judged) found the parallel build deeper, better cited, and stronger overall — yet it stamped "verified" on factual mislabels the single-context build avoided, and only an independent judge caught what self-consistency missed.
