---
name: github-review-pr
description: |
  Reviews a pull request in the current repository against the acceptance criteria of the issue or ADR it implements, and hands back one structured review comment for a human to post. Grounds every judgment in canonical state first — the integration branch tip and the linked design records — reproduces every fix claim by running the project's suites at the pull-request head in a throwaway worktree, and delegates the reading to fresh, stateless reviewer roles run in parallel: a blind reviewer that never sees the discussion, and a context verifier that checks each claim against the code. The comment opens with an explicit verdict, numbers its items continuously across review rounds, and leaves the merge with a human. Use when asked to review a pull request, re-review one after a round of fixes, verify a contributor's fix claims, or check a change before merge. Do not use for uncommitted local changes — that is the `/review` command — nor to draft or publish issues.
---

# Review a Pull Request (GitHub)

One responsibility: turn a pull request into a defensible verdict backed by reproduced evidence, packaged as comment text a human posts. The verdict comes from canonical state — the integration branch and the design records the change claims to implement — never from the pull request's own framing of itself, and never from what the reviewing session happens to remember. Nothing is believed that was not either read in canonical state or reproduced by a command whose exit code ends up in the comment.

## When to use / Skip if

**Use when:**

- A pull request in this repository needs review before merge.
- A previously reviewed pull request has a new round of fixes whose claims need re-verification.
- Someone states that a review finding is addressed, and the claim needs checking against the code.

**Skip if:**

- The change is uncommitted work in the local tree — that is the `/review` command; there is no pull request to ground against.
- The task is authoring or publishing an issue or ADR — `github-cr-issue`, `github-cr-adr`, `github-post-issue`.
- The ask is to merge, release, or back-merge — that is the release procedure (`docs/reference/releasing.md`), not a review.

Reviewer policy is out of scope: who reviews is decided by the repository, not by this skill. It enforces one staffing rule and no others — **the reviewer is not the author.**

## Step 0 — detect the repo and pin the target

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
[ -n "$REPO" ] || REPO=$(git remote get-url origin | sed -E 's#(git@|https://)github.com[:/]##; s#\.git$##')
N="${1:?pull request number}"
BASE=$(gh pr view "$N" --repo "$REPO" --json baseRefName -q .baseRefName)
```

Pass `--repo "$REPO"` on every `gh` command, so the review reads the repository the session is in rather than a hardcoded one.

## Phase 1 — Ground the review before judging anything

Nothing is assessed until canonical state has been read. In order:

| # | Read | How |
|---|---|---|
| 1 | The tip of the branch the change lands on — `develop` for ordinary work, `main` for release and hotfix pull requests | `git fetch origin && git log --oneline -1 "origin/$BASE"` |
| 2 | The pull request's own metadata, **including its author** | `gh pr view "$N" --repo "$REPO" --json title,body,author,baseRefName,headRefName,isDraft,mergeable,mergeStateStatus,files` |
| 2b | The discussion and every prior round — **for the context verifier only** | `gh pr view "$N" --repo "$REPO" --json comments,reviews` |
| 3 | The record it implements — the `Implements` / `Closes` line of the body | `gh issue view <record> --repo "$REPO"` |
| 4 | Every ADR the change or the record cites, with its status | `gh issue view <adr> --repo "$REPO"` |
| 5 | The acceptance criteria, **re-derived from steps 3–4** | read them out of the record; never copy the pull request's summary of them |

Design records are GitHub issues in this repository today; if they ever move into repository files, step 3–4 become a file read and nothing else in this phase changes.

Three rules make this phase load-bearing:

- **The reviewer is not the author.** Compare `author.login` from step 2 against the account this session acts as (`gh api user -q .login`); if they match, stop here and hand the review to someone else. Nothing downstream restores the independence a self-review gives up.
- **The record is the specification, the pull request is a claim about it.** A change that satisfies its own description while missing a criterion in the record is not done, and reading the criteria from the description would never reveal it.
- **No anchor, no review.** A pull request that links no issue or ADR and states no acceptance criteria gets `request changes`, with a single blocking item asking for the anchor. A change reviewed against its own claims always passes, which is the same as not reviewing it.

Record each ADR's status (`Proposed`, `Accepted`, `Rejected`, `Superseded`, `Deprecated`) — status decides how binding the conformance check in `references/checklist.md` is.

## Phase 2 — Stage the head in a throwaway worktree

Review the code as it will exist after merge, in isolation from the working checkout:

```bash
git fetch origin "pull/$N/head"
WT="$(dirname "$PWD")/$(basename "$PWD")-wt-pr${N}-review"   # absolute: Phase 4 cd's into it
git worktree add --detach "$WT" FETCH_HEAD
git -C "$WT" rev-parse --short HEAD          # pin every claim in the comment to this sha
git diff "origin/$BASE...FETCH_HEAD"
```

The three-dot diff shows what the branch adds, not what the base moved on to — a two-dot diff attributes other people's merged work to this author.

Remove the worktree once the comment is written: `cd "$ROOT"` first — Phase 4 leaves the session standing inside `$WT`, and `git worktree remove` / `git worktree prune` fail when run from inside the directory being removed — then `git worktree remove "$WT"` (add `--force` when the suites left artifacts behind), then `git worktree prune`. A worktree left on disk becomes a stale second checkout that the next review silently reads.

## Phase 3 — Dispatch the reviewer roles

The roles are **fresh subagents** that know only what this skill hands them. Session memory is not an input: a reviewer who remembers the last round inherits its conclusions and re-derives nothing. Launch them in **parallel from this session, never nested** — a role that spawns the other stops being independent of it. Prompt shapes: `references/reviewer-prompts.md`.

| Role | Receives | Never receives | Answers |
|---|---|---|---|
| **Blind reviewer** | the three-dot diff, the worktree path, the design records with discussion and author stripped, `references/checklist.md` | `gh`, `git log`, the pull-request discussion, prior review rounds, the author's identity | Does the change do what the record asked, and are the author's judgment calls the right ones? It looks hardest exactly there — the places where a reasonable implementer had to choose. |
| **Context verifier** | everything the blind reviewer gets, **plus** read-only `gh` (`view`, `checks`, `api` GET — never a call that writes), the pull-request discussion and every prior review round | the orchestrating session's own notes, drafts and conclusions — see "What no role gets" in `references/reviewer-prompts.md`, which binds every role | Is each fix claim true in the code? **It is the role that runs Phase 4** — the suites, the exact commands and exit codes, and the build story. |
| **Threat modeller** (add only when the change has a security surface: signing, secrets, supply chain, permissions, or anything that widens what runs or who may run it) | the blind reviewer's inputs **plus** a written threat-model brief: what the change is trusted to do, who could abuse it, what an attacker gains | the discussion, prior rounds, the author's identity | What breaks if the input, the environment, or the caller is hostile? |

Independence is the point: agreement between a role that saw the discussion and one that could not is evidence; agreement between two roles fed the same narrative is not. When they disagree, the disagreement goes in the comment — the blind reviewer's finding is not overruled just because the discussion explains it away.

## Phase 4 — Verify, do not trust

Every claim in the comment is either reproduced or dropped. The context verifier runs this phase in the worktree from Phase 2; the rest of this section is the specification it works from.

**Bootstrap first, or the exit codes mean nothing.** A detached worktree carries no virtual environments, so the component suites fall back to an interpreter that cannot import them and every exit code becomes noise. Build them **inside the worktree**, where the `Makefile` already prefers them and `**/.venv/` keeps them out of the drift check — and where removing the worktree disposes of them:

```bash
ROOT="$PWD"   # remembered so teardown can leave $WT before removing it
cd "$WT"   # every command in this phase runs here, never in the working checkout
python3 -m venv tools/spec-linter/.venv && tools/spec-linter/.venv/bin/python -m pip install -e 'tools/spec-linter[dev]'
python3 -m venv tools/spec-judge/.venv  && tools/spec-judge/.venv/bin/python  -m pip install -e tools/spec-linter -e 'tools/spec-judge[dev]'
```

Never install these editable into the ambient interpreter: the worktree is removed at the end of the review, and a global editable install is then left pointing at a path that no longer exists. Separately, `make check` needs `pytest` importable by the ambient `python3`, and `make lint` needs `shellcheck` on `PATH`. When `pytest` is not importable, do not reach for `make install-deps` — it installs into the machine's user site. Get the same coverage without mutating anything: `uv run --with pytest python3 -m pytest tests/ -q` followed by `python3 scripts/generate-agent-router.py --check`, or one more throwaway venv inside the worktree. A failure traced to a missing dependency is an environment result, reported as such; only a failure that survives a working environment is a finding about the change.

Every relative path below — the suites, the build, the drift check — resolves against the worktree because of that `cd`. Run them from anywhere else and the drift check reports the state of the working checkout instead of the pull-request head.

| Command | Covers | Read the result with care because |
|---|---|---|
| `make test` | the pytest suite (`tests/`), verbosely — the pipeline's own test step | — |
| `make check` | that same suite plus `python3 scripts/generate-agent-router.py --check` for agent-router drift | — |
| `make spec-lint` | the `tools/spec-linter` component tests | needs the editable install above |
| `make spec-judge` | the `tools/spec-judge` component tests (offline) | needs the editable install above |
| `tools/spec-judge/spec-judge --selfcheck` | the wrapper's cross-package import into `spec_linter` | `make spec-judge` runs the component tests only; this is the pipeline's separate step, and it never fires on a `develop`-base pull request |
| `make lint` | shellcheck over three shell scripts | it **exits 0 when shellcheck is not installed** — record its output, not just its exit code — and it does not cover `scripts/bump.sh`, which the pipeline lints separately; shellcheck that file by hand as well (`shellcheck -S warning scripts/bump.sh`) |
| `./build-plugin.sh && git diff --exit-code plugin/ .claude-plugin/` | plugin-mirror drift — see below | — |

Record the exact command and its exit code for each. "Tests pass" without a command is not evidence.

**The build is the only reconciler.** The committed `plugin/` tree is generated from `.claude/`, `plugin-extras/` and `tools/` by `./build-plugin.sh`; the drift check is the scoped `git diff --exit-code plugin/ .claude-plugin/` afterwards, which is exactly what the pipeline runs. Scope matters: the build regenerates the agent-router into `.claude/` before it copies, so a bare `git status` also surfaces that legitimate regeneration — along with any unrelated edit sitting in the tree — and would file all of it as a stale mirror. Two failure shapes to look for on any change that touches the build's sources: a non-empty diff after a rebuild (the committed mirror is stale), and anything in the shipped `plugin/` tree still referencing a file the build no longer produces.

**Local runs are the evidence, because most CI does not fire here.** Confirm what actually ran with `gh pr checks "$N" --repo "$REPO"`, then read it against this table:

| Base branch | Workflows that run | Consequence |
|---|---|---|
| `develop` | `bump-gate`, `e2e` | `Validate Plugin` and `Quality Checks` are scoped to `main`-base pull requests and never run — the test suite, the drift checks and shellcheck have no CI coverage on this pull request at all. The local runs above are the only evidence they pass. |
| `main` | `bump-gate`, `e2e`, and `Validate Plugin` + `Quality Checks` **when the change touches their path filters** | Release and hotfix pull requests are the first in a cycle to meet the full set, so they surface whatever `develop` accumulated. Only `bump-gate` and `e2e` are unfiltered: a `main`-base change touching only documentation fires neither of the other two. Read the checks column; do not assume it. |

**A conflicting pull request runs nothing.** With no merge commit to build, no workflow is triggered — so an empty or all-green checks column on a conflicting pull request means "nothing ran", not "nothing broke". Check `mergeable` / `mergeStateStatus` from Phase 1 before reading any checks column as a signal, and say so in the comment when it applies.

The version rule is a check, not a nit: a pull request into `develop` must leave `plugin/.claude-plugin/plugin.json` at `main`'s version. A bump on a `develop`-target pull request is blocking.

## Phase 5 — Synthesize one comment

Merge the roles' findings into a copy of the skeleton in `assets/review-comment-template.md`, drafted at `DRAFT="$(mktemp -t review-comment)"` — outside `$WT`, so Phase 2's teardown cannot delete it — never into the tracked asset itself. Resolve every duplicate; keep every disagreement. Every later reference to the draft uses `"$DRAFT"`.

1. **Heading.** `## Independent review — <one-line scope>`, or `## Independent re-review — <what was verified>` for a later round.
2. **Verdict line — first sentence, in bold, never buried.** Exactly one of:

   | Line | Means |
   |---|---|
   | `**Verdict: approve.**` | Nothing blocking, nothing worth a numbered item. |
   | `**Verdict: approve with changes.**` | Nothing blocking, but numbered non-blocking items stand — including any ADR inconsistency recorded rather than fixed. |
   | `**Verdict: request changes.**` | At least one blocking item. |

   A reader who stops after the first line must still have the answer.
3. **`### Verified`** — each claim with the command and exit code that reproduced it. On a re-review the heading carries the evidence conditions: `### Verified fixed (reproduced locally, isolated worktree at <sha>; <tool versions>)`.
4. **`### Blocking`** and **`### Non-blocking`** — numbered items; each names the location, the problem, and the fix. "Consider improving error handling" is not an item; "`build-plugin.sh`, the `REPO_LOCAL_SKILLS` array — the new repo-local skill is not listed, so the build ships it to consumers; append it" is.
5. **`### Not verified`** (optional) — what was not checked, and why. On a re-review, **`### Still open`** (optional) carries items from earlier rounds that nothing has changed.
6. **Closing line** — the merge decision stays with a human.

### Numbering across rounds — no goalposts moved

Item numbers are **continuous across every round of the same review**. Round 2 starts where round 1 stopped; a returning item is referred to by its original number, never renumbered. A finding that is genuinely new gets the next number and is marked as new, so nobody has to reconstruct whether it was there before.

An item is never silently re-scoped and never silently dropped. Dropping one is a statement: say it was fixed and how it was verified, or that it was wrong and why. An item that quietly grows between rounds turns a review into a moving target, and the author has no defense against it.

## What this skill never does

- **It does not approve, and it does not request changes through the API.** There is no state-changing pull-request call anywhere in this workflow. The output is comment text; a human posts it, and a human decides what it means for the merge.
- **It does not merge, close, or push.** Reading the repository and running the suites is the whole footprint — everything it writes lives inside the throwaway worktree, which Phase 2 removes.
- **It does not name who should review.** Only that the reviewer is not the author.
- **It does not carry conclusions between rounds.** Fresh roles, re-derived criteria, re-run commands — every round.

## References

| File | Read when |
|---|---|
| `references/checklist.md` | Phase 3–4 — the review dimensions the roles work through, including the ADR-conformance section and the blocking bar. |
| `references/reviewer-prompts.md` | Phase 3 — the prompt shape for each role, and exactly what each one is and is not given. |
| `assets/review-comment-template.md` | Phase 5 — the comment skeleton, first-round and re-review variants. |

## Related skills

- `github-cr-issue` · `github-cr-adr` — draft the records this review grounds itself in.
- `github-post-issue` — publishes those records; a blocking finding that deserves its own tracked issue is drafted and published there, not buried in the comment.
