# Issue templates (non-ADR)

Pick ONE type. The `` ## `[TYPE]` `` heading that opens each block below is a selector for navigating this file — it is never part of the issue body; the body starts at that block's first `## Summary`-style section. Title format: `[TYPE] <concise title>`. The body is **self-contained and formal** — no machine-local paths, no references to private working documents, no session-only context, no in-text labels. Set parent and related issues via GitHub's native sub-issue · "add parent" · relationship features, **not** inline `#NN` mentions. There is no epic template: draft a parent issue plus child issues and attach the children through native sub-issue relationships at publish time.

---

## `[FEATURE]`

## Summary
<What capability, for whom, and why now — one short paragraph.>

## Motivation
<The concrete problem or the value. What is painful or missing today.>

## Proposed approach
<High-level direction. If this needs an architecture decision, open an ADR (github-cr-adr) and reference it by its ADR number with the issue linked — don't decide architecture inside a feature issue.>

## Scope
- In scope: <…>
- Out of scope: <…>

## Acceptance criteria
- [ ] <verifiable outcome>
- [ ] <verifiable outcome>

---

## `[COMPONENT]`

## Summary
<The building block and its single responsibility — one line.>

## Role in the architecture
<Where it sits; what it consumes and produces; its boundary against sibling components.>

## Contract
<The interface the component commits to: inputs, outputs, and the invariants consumers can rely on. If an architecture decision governs this design, reference it by its ADR number with the issue linked — the decision holds the design; this issue tracks the build.>

## Deliverables
- [ ] Implementation and entry point
- [ ] Usage documentation
- [ ] Consumer wiring — whatever registers or exposes the component so its consumers can invoke it
- [ ] Tests

## Open questions
<Carried from the governing decision, if any.>

---

## `[TASK]`

## Summary
<The concrete unit of work — one line.>

## Definition of done
- [ ] <verifiable>
- [ ] <verifiable>

## Links
<Parent (feature / component / ADR) set via GitHub relationship. Development branch and PR linked here once they exist.>

---

## `[BUG]`

## Summary
<What is broken — one line.>

## Reproduction
1. <step>
2. <step>

## Expected vs actual
- Expected: <…>
- Actual: <…>

## Environment
<Anything needed to reproduce, stated self-containedly — OS / runtime / version / inputs. No machine-specific local paths.>

## Root cause / proposed fix
<If known; otherwise state it is under investigation.>

---

## `[SPIKE]`

## Question
<The single thing to investigate.>

## Timebox
<e.g. 1 day — a spike is bounded by design.>

## Why now
<What decision or downstream work this unblocks.>

## Deliverable
<What the spike produces: a recommendation, a decision input, a throwaway POC.>

## Done when
- [ ] <the question is answered, with evidence>
