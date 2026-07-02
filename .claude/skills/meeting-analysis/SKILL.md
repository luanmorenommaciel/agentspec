---
name: meeting-analysis
description: |
  Turns a meeting transcript into a validated analysis document — by delegating to the
  meeting-analyst agent — plus a short channel-ready follow-up message for the team's
  chat tool (Slack, Teams, Discord, or similar). Analyzes in the transcript's language,
  writes both artifacts in the team's working language, enforces document hygiene (no
  transcription meta, colleagues framed neutrally, length proportional to meeting
  substance, technical terms preserved exactly), and runs a grep-based leakage gate
  before delivery. Use whenever the user provides a meeting transcript, asks for
  meeting analysis, says "analyze this meeting", or wants a meeting summarized into
  shareable artifacts for the team. Do not use for daily standup messages — use
  `standup-report` — and do not use for raw transcript storage or cataloging.
---

# Meeting Analysis

Turn a meeting transcript into two shareable artifacts:

1. A formal **analysis document**, produced by the `meeting-analyst` agent with its
   10-section extraction framework (decisions, action items, requirements, blockers,
   implicit signals).
2. A short **follow-up message**, ready to paste into the team's chat channel.

Both artifacts are team deliverables. Hold them to that bar: formal, professional,
content only — nothing about how the analysis was produced.

## When to Use

- The user provides a meeting transcript (file path or pasted text) and wants it
  analyzed or summarized.
- The user asks to "analyze this meeting", "write up this meeting", or "summarize this
  for the team".
- The user wants a channel-ready post announcing meeting outcomes.

## Skip If

- The user wants a daily standup message — that is the `standup-report` skill (this
  skill can feed it; see step 7).
- The user only wants to store, file, or catalog a transcript, with no analysis
  requested.

## Core Heuristic: TL;DR Inline, Extra Documents Only When Needed

- The **inline TL;DR** (1–2 lines) always goes in the follow-up message itself. It is
  the at-a-glance "what you need to know", without padding.
- A **separate summary document** is justified only for very long (3h+) or unusually
  dense meetings. For everything else, the analysis document is enough. More documents
  do not add more value.

## Process

### 1. Gather Input and Context

Collect before delegating:

- **Transcript** — a file path or pasted text. If pasted, save it to a file first so
  the analyst agent can read it.
- **Meeting purpose** — what the meeting was for and, if the requester attended, what
  they say it resolved. This outcome lens tells the analyst where to focus.
- **Participants** — ask for a roster **only if** attribution matters for this meeting
  and the transcript leaves it unclear who said what. Machine transcripts often carry
  unreliable speaker labels; the requester's account of who attended and who decided
  beats the transcript. Do not interrogate the user when attribution is irrelevant to
  the outcomes.
- **Working language** — see step 2.

### 2. Set the Output Language

- **Analyze in the transcript's language.** Do not translate quotes or reasoning while
  extracting.
- **Write both artifacts in the team's working language.** Default to the transcript's
  language. When ambiguous — a mixed-language transcript, or signals that the team
  writes in a different language than it speaks — ask the user once, then proceed.
- Keep each artifact in a single language throughout.

### 3. Delegate the Analysis Document to `meeting-analyst`

Launch the `meeting-analyst` agent with:

- the transcript path,
- the context from step 1 (purpose, participants, outcome lens),
- the output language from step 2,
- the document-hygiene rules from step 4, passed verbatim — they are non-negotiable,
- the output location.

**Output location:** alongside the transcript (same directory) unless the user
specifies a path. Derive the filename from the transcript, for example
`2026-05-12-design-review-analysis.md` next to `2026-05-12-design-review-transcript.md`.

**Document structure** (suggest to the agent; omit empty sections): Executive summary ·
Decisions · Action items (owner + deadline) · Open questions · Next steps / timeline.

**QA return channel:** instruct the agent to return to you — separately, never in the
file — a one-paragraph synthesis, the decisions, the action items, and any attribution
ambiguities. Relay ambiguities to the requester as QA questions.

### 4. Enforce Document Hygiene

These rules are the value of this skill. Pass them to the agent and verify them
yourself before delivery.

| # | Rule | In practice |
|---|------|-------------|
| 1 | No transcription meta | The document contains only the meeting's content. No diarization or speaker-label notes, no confidence scores, no STT-quirk commentary, no narration of how attribution was reconstructed or corrected. |
| 2 | Ambiguities are QA, not content | "Attribution uncertain" hedging never appears in the document. Name a person only where attribution is safe; otherwise state the point without forcing a name. Open ambiguities go back to the requester as QA questions. |
| 3 | Neutral, professional framing | Nothing that could reflect poorly on a colleague (no "X barely spoke", no tone judgments). Describe contributions factually. |
| 4 | Proportional length | Short meeting = short document. Omit empty sections; never pad a section to look thorough. |
| 5 | Technical fidelity | Preserve technical terms exactly as used in the meeting: product names, code identifiers, file names, acronyms. Do not translate or paraphrase them. |

### 5. Run the Quality Gate

Before delivering, grep the generated document for transcription-meta leakage:

```bash
grep -inE "diariz|speaker [0-9]|confidence|STT|transcript label|attribution" path/to/the-analysis.md
```

- **Zero hits required.** Any hit means process meta leaked into a team deliverable.
- On a hit, fix with a surgical edit — do not regenerate the whole document — then
  rerun the grep until it comes back empty.
- The pattern matches English stems. When the document is written in another language,
  extend the pattern with that language's equivalent stems for the same concepts
  (diarization, speaker labels, confidence, attribution).
- The grep cannot catch tone. Also re-read how each participant is framed (hygiene
  rule 3) before delivering.

### 6. Generate the Follow-Up Message

Write a short post for the team's chat tool (Slack, Teams, Discord, or similar):

- **Shape:** 1–2 lines of context (which meeting, what it covered), an inline **TL;DR**
  with the central decision or outcome, and a pointer to the full analysis document.
- **Content discipline:** the TL;DR speaks only about the meeting's content — decisions
  and results. Never external metadata (file paths, "saved at", where it was posted).
- **Self-contained:** no meta-notes (nothing like "(no TL;DR because…)"), no apologies,
  no process narration.
- **Delivery:** hand the message to the user inside a fenced code block so it
  copy-pastes cleanly into the chat tool.
- **Long meetings:** for 3h+ or unusually dense meetings, also produce the separate
  summary document (same agent run) and mention it in the message.

Template:

```text
Follow-up from the {meeting description} on {date}: full analysis {attached / at LINK}.

TL;DR: {1–2 lines with the central decision or outcome}
```

Example:

```text
Follow-up from the payments design review on May 12: full analysis attached.

TL;DR: The retry queue ships behind a feature flag this release; the schema migration
is deferred until load-test results land (owner: platform team, due May 20).
```

### 7. Optional: Chain into the Standup Report

If the user also wants a daily standup message that references this meeting, do not
rebuild the context. Invoke the `standup-report` skill and hand it the participant
list and the meeting outcomes from this run, so the two artifacts stay consistent.
