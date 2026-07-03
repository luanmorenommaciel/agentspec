---
name: github-cr-adr
description: |
  Drafts an Architecture Decision Record (ADR) for the current repository: searches existing GitHub issues for duplicates first, applies a worthiness gate, then drafts from the context/decision/alternatives/consequences template with the standard status lifecycle, ready for publication as a GitHub issue. Use when the user asks to "create an ADR", "draft an ADR", "new ADR", "document an architecture decision", or to formalize an architecturally significant, hard-to-reverse technical choice. Do not use for routine feature or bug tracking — use `github-cr-issue`; publishing a drafted ADR to GitHub is `github-post-issue`.
---

# Create ADR (GitHub)

Draft one Architecture Decision Record as an ephemeral local file, ready to be reviewed and then published as a GitHub issue by `github-post-issue`.

An ADR records **one durable architecture decision** so it is never re-litigated from scratch. Its value is the **why** and the **trade-offs**, not just the final choice. The published ADR must stand alone: GitHub is the project's state store, agent sessions are stateless workers, and the issue is the complete record — any future contributor or agent session must be able to read it with zero private context.

This skill always operates on the repository it is invoked in — the repo is detected dynamically in step 1 and never assumed.

## When to use

- The decision is architecturally significant: it shapes structure, dependencies, interfaces, non-functional characteristics, or construction techniques.
- The decision is expensive to reverse, and a future contributor will need to understand why it was made.
- The user wants to formalize a decision already reached in discussion, so the reasoning survives the session.

## Skip if

| Situation | Do instead | Why |
|---|---|---|
| Feature, task, bug, spike, or epic | `github-cr-issue` | Routine work items are not architecture decisions. |
| Small, low-risk, easily reversible choice | Decide in the PR or issue thread | Log bloat drowns out the decisions that matter. |
| Temporary measure (POC, workaround, experiment) | Note it in the related issue | ADRs record durable decisions, not scaffolding. |
| Topic already covered by an existing ADR or standard | Comment on or amend the existing record | One decision, one record — duplicates fork the history. |

## Workflow

### 1. Search for existing coverage — before writing anything

Catching a duplicate before drafting costs one search; catching it at publish time costs a fully written body. Detect the consumer's repository dynamically:

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
# Fallback when gh cannot resolve the repo:
[ -z "$REPO" ] && REPO=$(git remote get-url origin | sed -E 's#(git@|https://)github.com[:/]##; s#\.git$##')

gh issue list --repo "$REPO" --search "<decision keywords>" --state all --limit 20
```

Search with `--state all`, because a closed or rejected ADR on the same topic is exactly the history that must not be forked. If `gh` is missing or unauthenticated, say so and continue drafting — dedup is a read-time optimization here and runs again as a hard gate at publish.

If an existing issue or ADR covers the topic, stop and propose one of these instead of a new draft:

- **Comment** on the existing issue with the new argument or evidence.
- **Amend** the existing ADR with a dated note (see the status lifecycle below).
- **Sub-issue** — a narrower follow-up decision linked to the existing record.

Continue to a new draft only when the topic is genuinely uncovered, or the user explicitly confirms the existing record does not apply.

### 2. Apply the worthiness gate — refuse, don't ask

An ADR is warranted only for a decision that is **architecturally significant and expensive to reverse**. If the request fails that bar, **decline to draft it** and explain why — do not draft anyway just because it was asked for, and do not soften the gate into a rhetorical question. Offer `github-cr-issue` for the same content as a regular issue, which is usually what the situation actually needs.

If the user insists after the refusal, ask for an explicit override rationale and record it in the draft's Context section, so the record itself explains why it exists.

Gate questions — all should be "yes":

| Question | Failing example |
|---|---|
| Does it change structure, interfaces, dependencies, or non-functional characteristics? | Renaming an internal helper function |
| Would reversing it later be costly? | A config flag that can simply be flipped back |
| Will a future contributor need the *why*, not just the *what*? | A choice fully explained by reading its diff |
| Is it durable, not a POC, workaround, or experiment? | A stopgap until the next release |

### 3. Gather the essentials

Ask the user for whatever is missing; never invent decision content.

| Element | Requirement | Why |
|---|---|---|
| Decision | One sentence, active present voice | Reads as a commitment, not an open debate. |
| Number | `ADR-XXX` placeholder, nothing else | The canonical number is the GitHub issue number — see Numbering. |
| Context / problem | Current state plus what exactly must be decided | Value-neutral facts let the reader judge the decision on merit. |
| Alternatives | Each option considered, plus why it was passed over | The "why not" proves the decision was weighed, not defaulted into. |
| Consequences | Both sides: what gets easier AND what gets harder | Only-upside consequences are a sales pitch, not a decision record. |

Decision statement, right and wrong:

```text
Good: "The service adopts event sourcing for order state."   (commitment, present voice)
Bad:  "We could maybe consider event sourcing at some point." (open debate, no decision)
```

### 4. Fill the template and save the draft

Copy `assets/adr-template.md`, fill every section, and save the draft:

```bash
mkdir -p .claude/sdd/drafts
# Save as: .claude/sdd/drafts/adr-<verb-phrase-slug>.md
```

The slug is a verb phrase in lowercase-with-hyphens (`adr-enforce-input-validation.md`, not `adr-validation-v2.md`) — a verb phrase names the decision itself, not the topic area.

**The draft is ephemeral.** It exists only to be reviewed and then consumed by `github-post-issue`, which deletes it after a successful publish. The published GitHub issue is the canonical record; never treat the local file as a source of truth after publication.

### 5. Run the self-containment pass

The published ADR must be readable with zero private context, so strip or translate before handing off:

| Remove | Replace with |
|---|---|
| Absolute or machine-local file paths | Repo-relative paths, only where a path is truly needed |
| Session references ("as we discussed", "per the call") | The actual content of what was discussed |
| Internal shorthand, codenames, nicknames | Self-explanatory names any stranger can follow |
| Links to private files or local drafts | Links to other GitHub issues or ADRs in the same repo |
| Process and tooling meta ("generated by…", "drafted during…") | Nothing — it carries no decision content |

### 6. Hand off for review and publication

Present the draft path and a short summary to the user for review. Publication belongs to `github-post-issue`: it re-runs the dedup and self-containment guardrails, validates labels, creates the issue, retitles it with the real ADR number, and deletes the draft.

Output of this skill: exactly one draft file under `.claude/sdd/drafts/`, or a reasoned refusal with a pointer to `github-cr-issue`.

## Content rules

| Rule | Why |
|---|---|
| One decision per ADR | A record covering two decisions cannot be superseded cleanly. |
| Formal, impersonal, active voice | The ADR becomes a public issue — a shared deliverable, not a chat log. |
| Concrete over vague; diagram (ASCII or Mermaid) when layout matters | Future readers cannot ask follow-up questions. |
| Consequences on both sides, always | Every real decision has a cost; a record without one is incomplete. |
| Alternatives with the explicit "why not" | Stops the same dismissed option being re-proposed later. |
| Fill Confirmation when verifiable | A decision with a check (test, lint rule, CI gate) enforces itself. |
| Keep it short — one to two pages | Long records do not get read; a big decision spawns smaller ADRs instead. |

## Numbering

The canonical ADR number **is the GitHub issue number**, assigned at publish time: `github-post-issue` retitles the issue to `[ADR-<issue#>] <title>` immediately after creation. Therefore:

- The draft carries the `ADR-XXX` placeholder and nothing else.
- Never pre-assign a number locally, and never treat a local number as truth — local numbering collides across sessions and forks, while the issue tracker is the only allocator that cannot.
- Cross-references to other ADRs always use their issue-assigned numbers.

## Status lifecycle

| State | Meaning |
|---|---|
| `Proposed` | Drafted, awaiting validation by the team |
| `Accepted` | Validated; the decision is in force |
| `Rejected` | Considered and declined — stays on record with the reasoning |
| `Superseded` | Replaced by a newer ADR, cross-linked both ways |
| `Deprecated` | No longer applies and has no direct replacement |

- A rejected ADR **stays on record** with its reasoning — it prevents re-litigating the same idea later.
- **Supersede, don't rewrite.** When an accepted decision changes, raise a new ADR that supersedes the old one, cross-link both, and mark the old one `Superseded by ADR-YYY`. Erasing the old reasoning erases the only defense against repeating the mistake.
- Because published ADRs are GitHub issues and therefore mutable, amending in place is acceptable for clarifications — but always with a dated note, never silently.

## References

| File | Read when |
|---|---|
| `assets/adr-template.md` | Filling in the draft (step 4) — copy it as the starting skeleton. |
| `references/adr-best-practices.md` | Unsure whether a decision deserves an ADR, or how to write a section well — the literature-grounded evidence base behind every rule above. |

## Related skills

- `github-post-issue` — publishes the reviewed draft as a GitHub issue, assigns the real ADR number, and deletes the draft.
- `github-cr-issue` — drafts regular (non-ADR) issues: features, tasks, bugs, spikes, epics.
