---
name: github-cr-issue
description: |
  Drafts the body of a well-formed, self-contained GitHub issue for the current repository from a per-type template — feature, component, task, bug, or spike — searching existing issues for duplicates before any drafting, and saving the result as an ephemeral draft ready for review and publication. Use when the user wants to create, draft, or write an issue, or asks for a feature, component, task, bug, or spike issue, or wants to turn an idea, defect report, or investigation into a tracked GitHub issue. For epic-scale initiatives it drafts a parent issue plus child issues joined by native GitHub relationships instead of an epic document. Do not use for architecture decisions — use `github-cr-adr`; to publish a draft to GitHub use `github-post-issue`.
---

# Create Issue (GitHub)

Draft the body of one well-formed, non-ADR issue as an ephemeral local file, ready to be reviewed and then published as a GitHub issue by `github-post-issue`.

A good issue records **one topic** in a **self-contained** way. GitHub is the project's state store, agent sessions are stateless workers, and the published issue is the complete spec — any future contributor or agent session must be able to read and act on it with zero private context.

This skill always operates on the repository it is invoked in — the repo is detected dynamically in step 1 and never assumed.

## When to use

- The user asks to create, draft, or write an issue — a feature, component, task, bug, or spike.
- A discussion, idea, or defect report needs to become a tracked, actionable GitHub issue.
- A large initiative needs structuring as a parent issue with sub-issues.

## Skip if

| Situation | Do instead | Why |
|---|---|---|
| Architecture decision (which option and why) | `github-cr-adr` | Features and components link to decisions; they do not contain them. |
| A finished draft needs publishing, labels, or relationships | `github-post-issue` | Publication has its own guardrails: dedup, self-containment, label validation. |
| Updating an issue that already exists | `gh issue comment` / `gh issue edit` | The existing issue is the record; extend it instead of forking it. |
| Trivial, immediate change | Fix it directly | An issue that outlives the work it describes is pure overhead. |

## Issue types

Pick exactly one type per issue.

| Type | Use for | Title format |
|---|---|---|
| `feature` | A capability to add, for users or developers | `[FEATURE] …` |
| `component` | A reusable building block or subsystem with a defined contract | `[COMPONENT] …` |
| `task` | A concrete unit of work, usually a child of a feature, component, or ADR | `[TASK] …` |
| `bug` | A defect, with reproduction steps and expected vs actual behavior | `[BUG] …` |
| `spike` | A time-boxed investigation: one question, one deliverable | `[SPIKE] …` |

**There is no epic template.** For an umbrella initiative, draft a parent issue (usually a feature) and separate child issues, then attach the children through GitHub's native sub-issue relationships at publish time. An epic written as a document duplicates state the child issues already carry and rots as they evolve; the relationship graph stays current because it is maintained where the work happens.

### Component issues

Use `component` when the deliverable is a reusable building block other work will consume, rather than an end-user capability. A component has a defined contract: one clear responsibility, named inputs and outputs, and an explicit boundary against sibling components. If the component's design still needs deciding, open the decision first with `github-cr-adr` and reference it by its ADR number with the issue linked — the decision holds the design; the component issue tracks the build.

The template's deliverables checklist is deliberately generic — implementation, documentation, consumer wiring, tests — so tailor each item to the repository's own layout when filling it in.

## Workflow

### 1. Detect the repository

The skill operates on whatever repository the user is working in — never assume an owner or name:

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
# Fallback when gh cannot resolve the repo:
[ -z "$REPO" ] && REPO=$(git remote get-url origin | sed -E 's#(git@|https://)github.com[:/]##; s#\.git$##')
```

### 2. Search for duplicates — before drafting anything

Catching a duplicate now costs one search; catching it at publish time costs a fully written body:

```bash
gh issue list --repo "$REPO" --search "<topic keywords>" --state all --limit 20
# e.g. for a retry mechanism on failed imports:
#   --search "retry import"   then   --search "failed ingestion"
```

Run the search two or three times with different keyword sets — title nouns, synonyms, the affected subsystem's name — because existing titles rarely match the new phrasing exactly. Keep `--state all`: a closed issue on the same topic is history the new one must acknowledge. If `gh` is missing or unauthenticated, say so and continue drafting — dedup is a read-time optimization here and runs again as a hard gate at publish.

On a hit, stop and propose one of these instead of a new draft:

| Overlap | Propose |
|---|---|
| An open issue already covers the topic | Comment on it with the new information, or edit its body to extend the spec |
| The topic is a piece of a larger existing issue | Draft it as a sub-issue of that parent |
| An existing issue is adjacent but genuinely distinct | Proceed, and record the relationship at publish time |

Continue to a new draft only when the topic is genuinely uncovered, or the user explicitly confirms the existing issue does not apply.

### 3. Pick the type and confirm the scope is one topic

Choose one type from the table above. If the request bundles several topics, split it — one issue per topic, or one parent with sub-issues — because a bundled issue cannot be closed, assigned, or prioritized cleanly. If the request is epic-scale, draft the parent and each child as separate files; the hierarchy is attached natively at publish time, never written into the bodies.

### 4. Copy the template block and fill it

Copy the matching block from `assets/issue-templates.md` and fill every placeholder. Keep the section headers inside the template exactly as given — a predictable structure is what makes issues scannable across the whole tracker. The `` ## `[TYPE]` `` marker line that opens each block is a selector for that file, not issue content — never include it in the body.

Per-type quality bar:

| Type | The draft is not done until |
|---|---|
| `feature` | Acceptance criteria are verifiable outcomes, not intentions |
| `component` | The contract names inputs, outputs, and the boundary against siblings |
| `task` | The definition of done is checkable by someone who did not do the work |
| `bug` | Reproduction steps are numbered and complete enough to run |
| `spike` | The question is single, the timebox explicit, the deliverable named |

### 5. Run the self-containment pass

The published issue must be readable with zero private context, so strip or translate before handing off:

| Remove | Replace with |
|---|---|
| Absolute or machine-local file paths | Repo-relative paths, only where a path is truly needed |
| References to private working documents ("see analysis #4") | The relevant content itself — a stray "#4" reads as a link to real issue number 4 |
| Session references ("as discussed", "per the call") | The actual content of what was discussed |
| Internal shorthand, codenames, nicknames | Self-explanatory names any stranger can follow |
| Process and tooling meta ("drafted during…") | Nothing — it carries no spec content |

Test: would a stranger who just cloned the repository understand and act on this issue alone?

### 6. Save the draft

```bash
mkdir -p .claude/sdd/drafts
# Save as: .claude/sdd/drafts/<type>-<slug>.md
```

The slug is the title in lowercase-with-hyphens (`feature-retry-failed-imports.md`), with no status markers or internal labels — the filename only needs to identify the draft until it is published.

**The draft is ephemeral.** It exists to be reviewed and then consumed by `github-post-issue`, which deletes it after a successful publish — the published issue is the canonical record, never the local file. A draft the author is not ready to take public stays in the file only; publishing is an explicit decision by whoever owns the issue.

Treat the drafts directory as a queue, not an archive — a draft that lingers unpublished should be published or deleted, because stale drafts drift from the tracker they were written for.

### 7. Hand off for review and publication

Present the draft path and a short summary to the user for review. Publication belongs to `github-post-issue`: it re-runs the dedup and self-containment guardrails, validates and applies labels, sets native parent/sub-issue relationships, creates the issue, and deletes the draft.

Output of this skill: one draft file per issue under `.claude/sdd/drafts/` — nothing is posted to GitHub.

## Content rules

| Rule | Why |
|---|---|
| Self-contained: readable with zero private context | GitHub is the state store; the issue is the complete spec for whoever picks it up next. |
| Native GitHub relationships, never a "Parent: #N" line in the body | A manual mention rots as the graph changes and can collide with a real issue number. |
| One topic per issue | An issue covering two topics cannot be closed, assigned, or prioritized cleanly. |
| No Labels line in the body | Labels are applied at publish time by `github-post-issue`; a hardcoded list drifts from the real ones. |
| Formal, impersonal, active voice; concrete over vague | The issue becomes a public record — a shared deliverable, not a chat log. |
| Reference ADRs by their ADR number, with the issue linked | A name like "the caching decision" is ambiguous; `ADR-003` is the stable citation, and the link makes it navigable. |

Add an ASCII or Mermaid diagram when layout matters — future readers cannot ask follow-up questions.

## References

| File | Read when |
|---|---|
| `assets/issue-templates.md` | Filling in the draft (step 4) — copy the matching type block as the skeleton. |

## Related skills

- `github-cr-adr` — drafts Architecture Decision Records; use it when the work is deciding an architecture, not building one.
- `github-post-issue` — publishes the reviewed draft: labels, relationships, guardrails, then deletes the draft file.
