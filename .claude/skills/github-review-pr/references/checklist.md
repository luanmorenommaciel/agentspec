# Review Checklist

The dimensions a reviewer role works through, and the bar that separates a blocking item from a non-blocking one. Handed to the roles in Phase 3; the conformance and verification sections are also what Phase 4 reproduces.

Work the sections in order. The first three decide whether the change is the right change at all; the rest decide whether it is a good one. A change that fails section 1 or 2 is not saved by passing everything below.

## 1. Anchor and acceptance criteria

| Check | Blocking when |
|---|---|
| The pull request names the issue or ADR it implements (`Implements` / `Closes`). | Nothing is linked and the body states no acceptance criteria — there is nothing to review against. |
| Every acceptance criterion in the record is satisfied by the diff. | A criterion is unmet, or met only in the description and not in the code. |
| Nothing in the diff is outside the record's scope. | Unrelated behavior changes ride along, so the record can no longer be closed by reviewing this change. |
| The criteria were re-derived from the record, not from the pull request's summary. | (Reviewer discipline — not an item; a review that skips this cannot find the two rows above.) |

Scope creep that is merely adjacent — a drive-by rename, an unrelated typo fix — is non-blocking, but it is named: it makes the change harder to revert as a unit.

## 2. ADR conformance

Every ADR the change cites, plus any ADR governing the area it touches, is read and its status recorded. Status decides how binding it is:

| ADR status | An inconsistency between the change and the ADR is |
|---|---|
| `Accepted` | **Blocking.** The decision is in force. Either the change conforms, or the ADR is superseded first — a change that quietly diverges makes the record lie about the system. |
| `Proposed` | **Blocking if the change presents itself as implementing that ADR** (it must implement what the ADR says). Otherwise an explicit numbered item under `approve with changes`, naming the divergence and asking which one moves. |
| `Superseded` / `Deprecated` | Non-blocking, but named: conforming to a retired decision is a signal the author read the wrong record. |
| `Rejected` | **Blocking.** The change implements something the project decided against; that needs a new ADR, not a pull request. |

An inconsistency is **never waved through silently.** It is blocking, or it is a numbered item under `approve with changes`. "The ADR is probably out of date" is a finding, not a reason to omit one.

Also check, for any change that touches design records themselves: an ADR is superseded, never rewritten; a number is never reused; a status transition (`Proposed` → `Accepted`) is recorded in the record, not inferred from the merge.

## 3. Contract and interface

- The public surface the record specifies is what the code exposes — names, arguments, return shapes, exit codes.
- Exit-code and verdict vocabularies are used as defined, not reinterpreted locally.
- A consumer of the changed surface elsewhere in the repository is updated in the same change, or the change is backward compatible. A half-migrated consumer is blocking.
- New configuration, flags or environment variables have a documented default and a defined behavior when absent.

## 4. Correctness

- Error paths exist and are distinguishable from success. A failure that exits zero is blocking.
- Failures are loud: an unavailable dependency degrades to a visible, named condition, never to a silent pass.
- Boundary conditions in the diff are handled — empty input, missing file, zero matches, first run.
- Nothing in the change depends on state that only exists on the author's machine.

## 5. Tests

- Every new behavior has a test that fails without the change. A test that passes on the base branch tests nothing.
- Tests assert on outcomes, not on log text or incidental formatting.
- The suites in Phase 4 pass at the pull-request head, and each run's exit code is recorded.
- A change that alters an existing test's expectations explains why the old expectation was wrong.

## 6. Build, mirror and CI reality

- `./build-plugin.sh && git diff --exit-code plugin/ .claude-plugin/` comes back clean — the scoped diff the pipeline runs, not a bare `git status`, which also surfaces the agent-router the build regenerates into `.claude/` and any unrelated edit in the tree. A non-empty diff after a rebuild means the committed mirror is stale: blocking on any change that touches the build's sources.
- Nothing in the shipped tree references a file the build no longer produces.
- A repo-local skill is listed in `REPO_LOCAL_SKILLS`; a distributed one is not. Getting this backwards ships contributor tooling to consumers, or drops a skill that was meant to ship.
- The checks column is read against the base branch: `develop`-base pull requests do not run `Validate Plugin` or `Quality Checks` at all, and a pull request that conflicts with its base runs nothing. Neither absence is evidence of health.
- A `develop`-base pull request leaves the version equal to `main`'s. A bump there is blocking.

## 7. Documentation and changelog

- User-visible changes carry a `CHANGELOG.md` entry under `## [Unreleased]`.
- Counts and catalogs stated in the documentation still match the filesystem after the change.
- Anything published outside the repository is self-contained: no machine-local paths, no private context, no internal shorthand a stranger cannot resolve.
- The documentation describes what the code now does, not what the change hoped to do.

## The blocking bar

An item is **blocking** when merging as-is would leave the repository in a state someone must undo: an unmet acceptance criterion, a conflict with an `Accepted` or `Rejected` ADR, a broken contract, a silent failure, a stale generated tree, a missing test for new behavior, a version bump on the wrong base.

An item is **non-blocking** when it is a real improvement that a follow-up can carry: naming, structure, a missing edge-case test on existing behavior, documentation polish, adjacent scope creep.

Two calibration rules:

- **Uncertainty is not severity.** What could not be checked goes under `Not verified`, phrased as what was not checked — never inflated into a blocking item, never quietly dropped. A failure traced to a missing dependency is an environment result and belongs there too, not in `Blocking`.
- **The bar is the repository's, not the reviewer's taste.** A preference with no rule behind it is non-blocking at most, and is labelled as a preference.
