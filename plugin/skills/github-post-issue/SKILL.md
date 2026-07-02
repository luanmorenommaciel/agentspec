---
name: github-post-issue
description: |
  Publishes a drafted issue or ADR to the current repository's GitHub board via gh, with guardrails, and curates the board safely. Runs a verdict-gated pre-flight before any write: duplicate search across open and closed issues, a self-containment lint, template conformance, and label validation against the live repo (human-in-the-loop for missing labels, never auto-created). Applies native parent/sub-issue relationships, assigns owners, closes (never deletes) superseded issues with a pointer comment, and deletes the local draft once the issue URL is returned. Use when the user wants to post or publish a drafted issue or ADR, apply labels, set parent/sub-issue relationships, assign an owner, or close/curate issues on the board. Do not use to draft content — use `github-cr-issue` or `github-cr-adr` first.
---

# GitHub Post Issue

Publish a drafted issue or ADR to GitHub via `gh`, with guardrails, and curate the board safely — one responsibility: hygienic mutation of the issue board. Authoring happens upstream (`github-cr-issue` / `github-cr-adr`); this skill is the `gh` write with checks around it, so nothing malformed, duplicated, or context-leaking reaches the public board. The recommended label taxonomy and its design rationale live in `references/label-scheme.md`.

## When to use / Skip if

**Use when:**

- A drafted issue or ADR is ready to publish — typically a file under `.claude/sdd/drafts/`.
- The user asks to apply labels, set a parent/sub-issue relationship, or assign an owner.
- The board needs curation: closing duplicates or superseded issues, re-triaging labels.

**Skip if:**

- The content still needs drafting or restructuring — use `github-cr-issue` / `github-cr-adr` first, then come back here.
- The request is read-only (`gh issue list`, `gh issue view`) — reads need no guardrails.
- The work is a pull request, not an issue — use the PR workflow instead.

## Step 0 — detect the repo (never hardcode)

Resolve the target dynamically so the skill works in whatever repository it is installed in:

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)   # preferred
[ -z "$REPO" ] && REPO=$(git remote get-url origin | sed -E 's#(git@|https://)github.com[:/]##; s#\.git$##')   # fallback — normalize the remote URL to owner/repo
```

Pass `--repo "$REPO"` on **every** `gh` command below. A hardcoded repo writes to the wrong board the day this skill runs in a different checkout.

## Input

Accept either form:

- **A draft file** — typically `.claude/sdd/drafts/<type>-<slug>.md`, produced by `github-cr-issue` or `github-cr-adr`. Preferred, because the draft is reviewable and diffable before it goes public.
- **In-conversation content** the user asks to publish. Write it to a draft file first so the same flow (and `--body-file`) applies.

Always publish the body with `--body-file <draft>` — inline `--body` strings mangle long markdown, since quoting, backticks, and newlines survive a file but not a shell argument.

## Pre-flight gate — before every `gh issue create`

Run four checks, **in this order**. Every finding gets a verdict:

| Verdict | Meaning |
|---|---|
| **BLOCKER** | Do not publish until fixed. |
| **IMPORTANT** | Warn the user; publish only with their explicit ack. |
| **NIT** | Note it and proceed. |

**A publish happens only with zero BLOCKERs.**

| # | Check | How | Failure → verdict |
|---|---|---|---|
| 1 | Dedup (open + closed) | `gh issue list --repo "$REPO" --search "<topic terms>" --state all` | Open issue already covers it → BLOCKER · overlap with a closed issue → IMPORTANT |
| 2 | Self-containment lint | Read the draft as a stranger with zero shared context | Leaked local paths, private-session references, internal codenames, or a `#NN` that is not a real issue → BLOCKER · vague but resolvable phrasing → NIT |
| 3 | Template conformance | Compare against the type's drafting template | Missing sections or acceptance criteria → IMPORTANT · missing `[TYPE]` title prefix → IMPORTANT · a `Labels:` line in the body → BLOCKER (remove it, then proceed) |
| 4 | Label validation | `gh label list --repo "$REPO"` | Intended label missing from the repo → BLOCKER until the user decides: create, substitute, or drop |

Why each check exists, in one clause:

1. **Dedup** — a duplicate splits the discussion and rots the board; comment on or update the existing issue, or attach the new one as its **sub-issue** instead.
2. **Self-containment** — the issue must stand alone for any contributor, human or agent, with no access to your session, filesystem, or private context.
3. **Template + no `Labels:` line** — consistent structure keeps issues scannable, and labels belong on the issue object; a prose copy drifts from the real labels immediately.
4. **Label validation** — the live repo is runtime truth and the scheme file is only intent; if a wanted label does not exist, **surface it and ask** before running `gh label create`. Never auto-create a label and never apply a phantom one — silent board mutation is exactly what this gate prevents.

## Publish flow

1. **Gate.** Run the pre-flight above. Fix every BLOCKER, get explicit ack on each IMPORTANT, note NITs.
2. **Create.**

   ```bash
   gh issue create --repo "$REPO" --title "[TYPE] <title>" --body-file <draft.md>
   ```

   Capture the returned URL and issue number `<n>`.
3. **Labels** — apply only labels validated in gate check 4:

   ```bash
   gh issue edit <n> --repo "$REPO" --add-label "type:<x>,priority:<p>"
   ```

   Add `blocked` / `needs-decision` only while actually true — a stale status flag misleads everyone who filters by it.
4. **Ownership = assignee, not a label.** When someone is actually going to work the issue:

   ```bash
   gh issue edit <n> --repo "$REPO" --add-assignee <github-handle>
   ```

   Infer the assignee's GitHub handle from context — the user's request, `git log`, existing issues — or ask. Never guess a handle.
5. **Parent / sub-issue = native relationship.** Attach a task, bug, or spike under its parent feature or component issue using GitHub's sub-issue feature (the UI, or the sub-issue GraphQL mutations via `gh api`). Never write `Parent: #42` in the body — prose relationships never update and do not render as a tree.
6. **Receipt, then draft cleanup.** Print the issue URL as the receipt. On success, **delete the draft file**: the published issue is now canonical and re-fetchable (`gh issue view <n> --repo "$REPO"`), so a lingering local draft is drift waiting to happen. If the publish failed, keep the draft — it is the only copy.

## ADR flow — numbering made mechanical

An ADR publishes exactly like an issue, plus the `type:adr` label. **The canonical ADR number is the issue number** GitHub assigns at creation — no side counter to maintain, so numbering cannot drift. Enforce it immediately after `gh issue create`:

1. Create from the draft as usual (a placeholder title like `[ADR-XXX] <title>` is fine at this point) → GitHub returns issue number `<n>`.
2. Retitle with the real number:

   ```bash
   gh issue edit <n> --repo "$REPO" --title "[ADR-<n>] <title>"
   ```

3. If the published body still contains an `ADR-XXX` placeholder, replace it: fetch the body (`gh issue view <n> --repo "$REPO" --json body -q .body`), substitute `ADR-XXX` with `ADR-<n>`, write the result to a file, and push it back:

   ```bash
   gh issue edit <n> --repo "$REPO" --body-file <updated.md>
   ```

4. Receipt + draft cleanup, exactly as in the publish flow.

A `Rejected` ADR is **closed, never deleted** — it stays on record so the idea is not re-litigated from scratch.

## Curate — close, never delete

Close > delete. Deleting is permanent, admin-only, and destroys history and cross-references; closing as not-planned or duplicate keeps the trail searchable. Even for pure noise, closing is the safer default.

- **Superseded / duplicate** — close with a one-line pointer to the canonical issue; the pointer is what keeps the trail navigable:

  ```bash
  gh issue close <n> --repo "$REPO" --reason "not planned" \
    --comment "Superseded by #<canonical> — <one-line reason>."
  ```

- **Relabel / re-triage** — `gh issue edit <n> --repo "$REPO" --add-label … --remove-label …`; validate any label you add (gate check 4) first.
- **Rejected ADRs** — close with a comment recording the rejection reason; keep the title and label intact so the record stays findable.

## DO / DON'T

**DO**

- Detect the repo dynamically and pass `--repo "$REPO"` on every command — the skill must work in any repository.
- Run the full pre-flight gate before every create; zero BLOCKERs or no publish.
- Publish bodies via `--body-file`.
- Apply only labels that exist in the live repo.
- Use assignees for ownership and native sub-issues for grouping.
- Close with a pointer comment; keep one topic per issue.
- Print the issue URL as the receipt, then delete the local draft.

**DON'T**

- Hardcode a repository or owner.
- Open a duplicate — comment, update, or attach as a sub-issue instead.
- Delete an issue. Ever.
- Put `Parent: #42` or a `Labels:` line in the body.
- Apply a phantom label, or create a missing one without explicit user confirmation.
- Leak local paths, session context, or internal codenames into a public issue.
- Keep the draft file around after the issue URL comes back.

## Reference

- `references/label-scheme.md` — recommended label taxonomy and the design rules behind it: status-is-not-a-type, ownership-by-assignee, grouping-by-sub-issues, and the drift rule.
