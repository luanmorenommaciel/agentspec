---
name: standup-report
description: |
  Generates the user's daily standup message in the Done / Will do / Blockers format from git history, PRs/issues, and the user's own notes, ready to paste into the team chat, with an optional short follow-up thread for extra detail. Use when the user asks for "standup", "my check-in", "daily update", or to put together the day's status message for the team. Do not use for meeting summaries — use `meeting-analysis` — or for status reports longer than a standup; write those as documents.
---

# Standup Report

Generate the user's daily standup message: what moved forward, what comes next, and what is blocked. Assemble evidence from the repository and the user's own account, draft the three-section message, confirm it with the user, and deliver it ready to paste into the team's chat tool (Slack, Teams, or whatever the team uses).

A standup is a pulse, not a report. The format is lightweight — a greeting and emoji markers are fine — but the substance stays concrete, verifiable, and honest.

## When to use

- The user asks for a standup, check-in, daily update, or the day's status message.
- The user wants yesterday's work and today's plan summarized for the team chat.

## Skip if

- The input is a meeting transcript or the user wants a meeting summarized — use `meeting-analysis` instead.
- The user needs a status update longer than a standup (weekly summary, retrospective, project report) — write those as documents, not chat messages.

## Message template

```
<optional greeting line — e.g. "Good morning, team! Daily check-in:" — with the team @-mention if the user wants one>

🟢 **Done**
- <concrete verb + artifact, one line — e.g. "Merged PR #118 — retry handling in the sync client">
- <2–4 bullets per section>

🟡 **Will do**
- <next meaningful deliverable, one line — e.g. "Open the follow-up PR wiring retries into the batch endpoint">

🔴 **Blockers**
- <what is blocked + what is needed + from whom (by role), one line — or exactly "No blockers today.">
```

Example, filled:

```
Good morning, team! Daily check-in:

🟢 **Done**
- Merged PR #118 — retry handling in the sync client
- Opened PR #123 — pagination for the export endpoint
- Published the draft rollout plan for team review

🟡 **Will do**
- Start the auth-module migration once PR #123 lands
- Turn rollout-plan feedback into the final checklist

🔴 **Blockers**
- PR #123 (pagination for the export endpoint) awaits reviewer feedback — blocks the migration start
```

### Formatting rules

- **One line per bullet.** Never hard-wrap inside a bullet — chat tools soft-wrap, and a hard-wrapped bullet renders as broken fragments.
- **2–4 bullets per section.** More than that is a report, not a pulse — move the overflow to the thread or cut it.
- **Blank line between sections** — the message breathes better.
- **The 🟢/🟡/🔴 markers and bold section headers are the format's identity — keep them.** If the team's chat tool renders emoji shortcodes more reliably than literal emoji, swap them at delivery time.
- **Team @-mention is optional and never assumed.** If the user wants one, ask for the exact group handle — do not invent or guess it.
- **Greeting matches the time of day**, and is optional.
- **Inline links where the chat renders markdown**: a labeled link to a PR or issue beats a raw URL. In **Blockers**, make the link label descriptive enough that the reader grasps what is blocked without clicking.
- **Joint work reads in the plural, solo work in the singular.** "We aligned on the rollout plan" credits the team; "I opened the PR" owns the work. Do not claim shared work as solo, and do not dilute solo work into "we".
- **No blockers? Say so explicitly** ("No blockers today.") — never invent one to fill the section.

## Assemble the content

1. **Identity.** Derive the author from `git config user.name` (and `user.email` for log filtering). If unset or ambiguous, ask the user. Never hardcode a person.
2. **Window.** Done covers the span since the last standup — default: yesterday plus today so far. Will do covers the next working day.
3. **Git history.** Run `git log --oneline --since="yesterday" --author="<name>"` in the current repository, plus any other repositories the user names.
4. **PRs and issues.** When `gh` is available and the repository is on GitHub, pull the user's recently merged and open PRs (`gh pr list --author "@me" --state merged` / `--state open`) and recently closed or assigned issues (`gh issue list --assignee "@me"`). If `gh` is missing or errors, skip this source silently — it is an enrichment, not a requirement.
5. **User-pointed sources.** Read whatever task list, tracker export, or planning file the user points at. Do not guess paths and do not crawl the workspace looking for one.
6. **The user's own words.** Ask what the artifacts do not show: reviews given, meetings held, decisions made, teammates unblocked, direction changes.
7. **Draft, then confirm.** Always show the assembled draft and confirm it with the user before final delivery — artifacts under-report the day, and the user knows what actually happened.

## Quality rules

| # | Rule | Why |
|---|------|-----|
| 1 | Done bullets use concrete, verifiable verbs anchored to artifacts — "opened PR", "merged", "published", "fixed" — never "worked on" or "looked into". | Vague verbs hide state. |
| 2 | Verb proportional to the work: "refined" ≠ "reworked" ≠ "rebuilt" — pick the smallest verb that is still true. | Inflated verbs erode trust. |
| 3 | Will-do items sit at deliverable altitude — the next meaningful outcome, not micro-actions like "reply to a review comment". | Teammates read outcomes, not todo lists. |
| 4 | Report state at posting time: if something changed since yesterday's plan, write the current truth, not the stale intention. | Stale intentions misdirect the team. |
| 5 | Never cite CI or test status as an accomplishment. | Green tests are table stakes, not progress. |
| 6 | "Decided" / "closed" only for decisions actually made; "discussed" / "aligned" for conversations that set direction. | Conflating them creates phantom commitments. |
| 7 | Waiting on review or feedback IS a blocker — name it honestly, with what is needed and from whom (a role, not a personal callout). | Unnamed waits stall work silently. |
| 8 | An honest thin day beats a padded one. | Padding is visible and costs credibility. |

Two further checks before showing the draft:

- **Will do lists only what the user owns.** A teammate's deliverable or a team-wide goal does not belong there; the user's own coordination step toward it ("raise the cutover date with the platform team") does.
- **Cut execution parentheticals.** A detail like "(rebase expected, no conflicts)" belongs in the PR, not the pulse — if it matters, move it to the thread.

Apply the rules while drafting, not as an afterthought — most rewrites come from inflated verbs (rule 2) and missing review-wait blockers (rule 7).

## Optional detail thread

- When one item genuinely needs context — links, error detail, design rationale, material to attach — offer a short follow-up thread message instead of bloating the main message.
- Threshold: one or two extra details belong in the bullet itself; a thread is only for genuinely dense material.
- Thread format: free-form and short. It does not repeat the Done / Will do / Blockers structure. Title it with the date and topic.

Example thread message:

```
Thread — <date>: export-endpoint pagination

Context for PR #123: went with cursor-based pagination over offset — offset scans degraded badly past large row counts.
Benchmark numbers and the query-plan comparison: <link>
Client impact: none — the old offset params keep working until the next major version.
```

## Delivery

- Put the final message in a fenced code block, ready to select and paste into the chat. Never deliver it as a blockquote or decorated markdown — terminal border characters contaminate the copy-paste.
- If a thread was drafted, deliver it in its own separate fenced block after the main message.

## Persistence

- Default is message-only: deliver the text and stop.
- If the user keeps a standup history directory, offer once to save a copy there — ask for the location the first time, then reuse the answer without re-asking.
- When saving: one file per day, named by date (e.g. `YYYY-MM-DD.md`), containing the message and the thread if there is one. If the day's file already exists, update it rather than duplicating.

Saved-file layout:

```
# Standup — YYYY-MM-DD

## Message
(the message exactly as delivered)

## Thread (optional) — "topic"
(the thread text)
```
