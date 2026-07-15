# ADR Best Practices — Cited Reference

**Purpose.** Evidence base for the `github-cr-adr` skill. Every design choice in that skill traces back to a standard documented here. Researched 2026-06-15 against the canonical sources listed at the bottom.

## What an ADR is

An ADR captures **one architecturally-significant decision** together with its **context, the decision, and its consequences**. This triad is consensus across every source.

- Nygard: a short text file documenting decisions that affect "the structure, non-functional characteristics, dependencies, interfaces, or construction techniques."
- AWS: "Each ADR describes the architectural decision, its context, and its consequences." Minimum bar: "the context of the decision, the decision itself, and the consequences."
- Purpose: preserve the **why** so future readers neither blindly accept nor blindly reverse past decisions (Nygard). Focus on the *reason*, not the implementation — that is what stops later architects, who weren't in the room, from overruling a decision they don't understand (AWS).

## The yardstick — core sections

Audit any ADR against these. The first five are unanimous; an explicit alternatives section is present everywhere except Nygard's original (which folds it into Context).

| Section | What it holds |
|---|---|
| Title | short phrase, one decision |
| Status | lifecycle state (see below) |
| Context | value-neutral facts / forces motivating the decision |
| Decision | the response, in active voice ("We will…") |
| Consequences | the resulting context — **positive AND negative** |
| Alternatives + trade-offs | options weighed + **why each was rejected** |

Optional but recommended by ≥2 sources: decision drivers/criteria; a **Confirmation / Compliance** section (how the decision will be verified — tests, fitness functions); metadata (date, deciders).

## Best practices (with the why)

- **Preserve the rationale history.** *Invariant (unanimous):* never silently rewrite a decision; never leave a reversed one marked `Accepted`. *Mechanism (varies):* supersede with a new ADR + cross-link, flipping the old one to `Superseded` (Nygard / AWS / adr-tools) — OR amend in place with a dated note ("living document," the joelparkerhenderson repo's own pragmatic stance: "in practice mutability has worked better for our teams"). For issue-based ADRs (mutable by nature), amend-and-cross-link fits the medium.
- **One decision per record** (adr.github.io: "a single AD").
- **Decision in active, present voice** — "We will…" reads as commitment, not open debate (Nygard).
- **Always capture alternatives + their trade-offs.** The Y-statement grammar forces it: "…we decided for X and neglected Y, to achieve Z, accepting W." Documents completeness and stops dismissed options being revisited (Zimmermann).
- **Consequences must include the downside.** A record with only upside is a sales pitch — Nygard mandates negative consequences; the Y-statement forces an "accepting that…" clause.
- **Sequential, never-reused numbering** → stable, citable forever (Nygard). Note: joelparkerhenderson uses verb-phrase slugs with no numbers — numbering is template-dependent, not universal.
- **Store in-repo, as versioned Markdown, next to the code** — it stays in sync with the code, unlike a wiki (ThoughtWorks — the reason lightweight ADRs are rated *Adopt*).
- **Keep it short (1–2 pages); expand only where the option space genuinely needs it** (Nygard; Tyree allows diagrams and long explanations for the Positions section).
- **Write for a future reader who lacks today's context** — the unifying *why* behind all of the above.

## Anti-patterns

- Decision recorded with no context, or no consequences.
- Pseudo-rationale / "killer phrases" — "everybody does it," "we've always done it that way" (Zimmermann). Cite real requirements and evidence instead.
- No "why not" — alternatives missing.
- One-sided consequences (no downside recorded).
- Editing an accepted decision so the original reasoning vanishes.
- Stale log — a superseded decision left marked `Accepted`.
- Log bloat — don't document everything; only what is hard and costly to change (Zimmermann: a log >100 entries "will probably put readers to sleep").
- Wrong medium — a wiki/spreadsheet that drifts out of sync with the code.

## When to write one (granularity)

Write an ADR when a future contributor will need the **why** of an architecturally-significant, costly-to-reverse choice. **Don't** write one for: non-architectural decisions; tiny / low-risk / single-developer choices; temporary things (POC, workaround, experiment); or anything already covered by an existing standard/doc. A big ADR is expected to *spawn* smaller ADRs rather than absorb them.

## Status lifecycle

There is no single mandated enum. The widely-used default (Nygard): **Proposed → Accepted / Rejected → Superseded / Deprecated**. Keep rejected ADRs along with the reason — it stops the same idea being re-litigated. Exact labels vary by template; the rule is "pick one and stick to it" (Zimmermann).

## Template catalog (for reference)

The joelparkerhenderson repo catalogs ~13 templates. The ones worth knowing:

- **Nygard** — the 5-part baseline (Title / Status / Context / Decision / Consequences). Everything else elaborates it.
- **MADR** (Markdown Any Decision Records) — Context & Problem · Decision Drivers · Considered Options · Decision Outcome · Consequences (`Good / Bad / Neutral, because…`) · **Confirmation** · Pros & Cons per option. YAML frontmatter: status / date / decision-makers / consulted / informed.
- **Tyree-Akerman** — most exhaustive (14 fields): Issue, Positions, Argument, Implications, Related-*.
- **Y-statements** (Zimmermann) — a one-sentence grammar; forces alternatives + downside onto a single line.

## Sources

- Michael Nygard (2011), "Documenting Architecture Decisions" — https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- joelparkerhenderson ADR collection — https://github.com/architecture-decision-record/architecture-decision-record
- MADR — https://adr.github.io/madr/ · adr.github.io — https://adr.github.io/
- AWS Prescriptive Guidance, "ADR process" — https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html
- ThoughtWorks Technology Radar, "Lightweight Architecture Decision Records" (Adopt) — https://www.thoughtworks.com/en-us/radar/techniques/lightweight-architecture-decision-records
- Olaf Zimmermann, "Y-Statements" — https://medium.com/olzzio/y-statements-10eb07b5a177 · "Architectural Decisions — The Making Of" — https://ozimmer.ch/practices/2020/04/27/ArchitectureDecisionMaking.html
- Tyree & Akerman template (faithful copy) — https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-jeff-tyree-and-art-akerman/index.md
- Richards & Ford, *Fundamentals of Software Architecture* (ADR chapter) — https://www.oreilly.com/library/view/fundamentals-of-software/9781098175504/
- Nat Pryce, adr-tools — https://github.com/npryce/adr-tools
