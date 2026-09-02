# Review Comment Template

Two skeletons — first round and re-review — plus the rules that govern both. Fill one in at Phase 5 and hand the result to the human who will post it. Angle-bracket text is a placeholder; delete every section that has no content rather than shipping an empty heading.

---

## First round

```markdown
## Independent review — <one-line scope: what this change does, in the reviewer's words>

**Verdict: approve with changes.**

Reviewed against <record> (<its acceptance criteria in one clause>) and <ADR-NNN, status>. Worktree at `<short sha>`, base `<base branch>` at `<short sha>`.

### Verified

| Claim | Command | Exit | Result |
|---|---|---|---|
| <the suite passes at the head> | `make check` | `0` | <27 passed; agent-router up to date> |
| <the generated tree is in sync> | `./build-plugin.sh && git diff --exit-code plugin/ .claude-plugin/` | `0` | <clean> |
| <criterion 3 of the record is met> | `<command, or the file and line that shows it>` | `<code>` | <what came back> |

<One line naming which CI workflows ran on this change and which did not, when that matters — e.g. a change into the integration branch where the main-only jobs never fire, or a conflicting change where nothing ran at all.>

### Blocking

1. **`<path>:<line>` — <the problem in one clause>.** <Why it blocks: what is left broken if this merges.> Fix: <the specific change>.
2. **<location> — <problem>.** <Consequence.> Fix: <change>.

### Non-blocking

3. **<location> — <problem>.** <Why it is worth doing, and why it can wait.> Fix: <change>.
4. **<location> — <problem>.** Fix: <change>.

### Not verified

- <What was not checked, and why — an environment that could not be reproduced, a surface out of scope for this round.>

The merge decision stays with <the maintainers>; this comment is a review, not an approval.
```

---

## Re-review

```markdown
## Independent re-review — <what was verified this round>

**Verdict: approve with changes.**

Round <n>. Items 1–<k> are from the previous round(s); numbering continues from there.

### Verified fixed (reproduced locally, isolated worktree at <short sha>; <tool versions — e.g. python 3.12.7, shellcheck 0.10.0>)

| # | Item | How it was verified | Exit |
|---|---|---|---|
| 1 | <the previous round's item 1, restated in one clause> | `<command>` | `0` |
| 2 | <item 2> | `<command or file:line that now shows the fix>` | `0` |
| 3 | <item 3> | <what was read or run> | `<code>` |

### Blocking

<None, or the still-open items by their original numbers.>

### Non-blocking

5. **<location> — <problem>.** <New this round: <why it appears only now — the fix for item 2 introduced it / this area was not in the previous diff>.> Fix: <change>.

### Still open

- **Item 4** — <unchanged since round 1; restate it in one clause and say what is needed to close it.>

The merge decision stays with <the maintainers>.
```

---

## Rules the skeletons encode

**The verdict is the first sentence.** Exactly one of `**Verdict: approve.**`, `**Verdict: approve with changes.**`, `**Verdict: request changes.**` — bold, on its own line, directly under the heading. No preamble, no thanks, no summary before it. A reader who stops after that line still has the answer.

**Every verified claim carries its command and exit code.** A claim without one is not verified; move it to "Not verified" and say so. On a re-review the heading itself states the evidence conditions — reproduced locally, in an isolated worktree, at a named sha, with the tool versions — because "it works for me" and "it works at `<sha>` under `python 3.12.7`" are different claims.

**Numbers are continuous across rounds and never re-used.** Round 2 continues where round 1 stopped. A returning item keeps its original number; a genuinely new one takes the next number and says it is new, with a word on why it appears only now. No goalposts moved: an item is never silently re-scoped, and never silently dropped — it is closed with evidence, or withdrawn with a reason.

**Items are specific and actionable.** Location, problem, fix. If the fix cannot be named, the item is a question, and it belongs in "Not verified" or in the body of the review as a question — not in a numbered list the author is expected to work through.

**An ADR inconsistency is always visible.** It is a blocking item, or it is a numbered item under `approve with changes` naming the divergence and asking which side moves. It is never omitted because the record looks outdated.

**The closing line hands the decision back.** The comment ends by saying the merge stays with a human. Nothing in this workflow approves, requests changes through the API, or merges.
