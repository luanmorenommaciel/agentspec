# Label Scheme — Recommendation and Rationale

A recommended label taxonomy for repositories using this skill's publish flow — and, more importantly, the design rules behind it. Adapt the values to your project; keep the rules, because they are what stop a board from rotting.

> **Drift rule.** This file documents *design intent*. The live repository's labels (`gh label list --repo "$REPO"`) are *runtime truth*. Validate that a label exists before applying it, and create a missing label only with explicit user confirmation — never assume this file and the repo are in sync.

## Recommended labels

| Label | Values | Meaning |
|---|---|---|
| `type:*` | `feature` · `component` · `task` · `bug` · `spike` · `adr` | The kind of work. **Exactly one per issue.** |
| `priority:*` | `p0` · `p1` · `p2` | `p0` = now/blocking · `p1` = soon · `p2` = backlog. A `high` / `medium` / `low` set works equally well — pick one vocabulary and never mix the two. |
| `phase:*` | `backlog` · `spec` · `design` · `build` · `review` · `ship` | Lifecycle stage. Naming the axis `status:*` works too — pick one name and keep a single lifecycle axis. |
| `blocked` | — | Work is blocked. Pair it with a comment naming the blocker, so the flag is actionable. |
| `needs-decision` | — | Awaiting a decision. @-mention the decider in a comment, so the flag has an owner. |

Variant: if you prefer GitHub's built-in `bug` label for defects, use it *instead of* `type:bug` as the type marker — one convention, applied consistently, is the only requirement.

## Design rules

### Status is not a type

`type:*` answers "what kind of work is this?" — and that answer never changes over the issue's life. Status ("blocked", "waiting on a decision", "in review") changes constantly. Encoding status as a type is how taxonomies rot: the label outlives the condition, and then the board lies. Hence exactly one `type:*` per issue, with lifecycle carried by the separate `phase:*` (or `status:*`) axis and transient conditions carried by the `blocked` / `needs-decision` flags, which are removed the moment the condition clears.

### Ownership by assignee, not by label

Capture ownership with GitHub **assignees**, never a label. A team- or group-label encodes an ephemeral org mapping as a permanent stamp: groups get redefined as the project evolves, and the label silently goes stale — the same failure mode as status-as-type. Assignees are person-based; a person's identity survives reorgs, so ownership stays accurate with zero maintenance. Assign when someone is *actively working* the issue, not as a permanent owner stamp. If a mutable org-level *view* is ever wanted, put it in a GitHub Project field — built to be reorganized — not in a label on the issue.

### Grouping by native sub-issues, not by label

Group related work with GitHub's native **parent/sub-issue relationships**: a `component` or `feature` issue is the parent; its tasks, bugs, and spikes are sub-issues. The parent issue is the stable anchor, and the grouping lives in the relationship graph — not in fragile prose `#NN` mentions that never update, and not in labels. A stable `area:*` label set (e.g. `area:ingestion`, `area:docs`) is a deliberate *future* option: add it only if board filtering becomes painful as the issue count grows. Until then, sub-issues plus the parent issue cover it — fewer labels means less to keep honest.

### Titles

`[TYPE] <concise title>` — e.g. `[FEATURE] …`, `[BUG] …`, `[ADR-001] …`. The bracket prefix keeps the title self-describing in every surface where labels are not rendered: notifications, cross-references, and search results. ADR numbers are sequential from 1, allocated from the live board at publish time — see the ADR flow in `SKILL.md` for the mechanical retitle step.

### The drift rule, restated

Never apply a label straight from this file. Run `gh label list --repo "$REPO"` first; if a wanted label is missing, surface it to the user and ask before running `gh label create`. Automatic label creation is silent board mutation — exactly the class of write the publish guardrails exist to prevent.
