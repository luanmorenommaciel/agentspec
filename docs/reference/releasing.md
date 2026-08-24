# Releasing

Maintainer procedure for cutting a release. Contributors do not need this document — see
[`CONTRIBUTING.md`](../../CONTRIBUTING.md), which covers everything required to open a pull request.

## Branch topology

| Branch | Role |
|---|---|
| `develop` | Integration branch. All feature, fix and documentation work lands here. Its version always equals `main`'s. |
| `release/X.Y.Z` | Short-lived, cut from `develop` when a release is prepared; the version for that release is raised here. Deleted once the release is merged and back-merged. |
| `main` | Released code. It receives release PRs from `release/X.Y.Z` branches, and hotfixes. Every commit on it is a candidate release point. |

`develop` was cut from the `v3.5.0` tag. A tag is created for every release and never moved.

The version moves on the release branch — and on a hotfix branch, see [Hotfixes](#hotfixes) — never on `develop`.
Raising it on `develop` breaks the equality with `main` that the gate checks on every pull request
against `develop`, so all of them fail at once whatever they contain — and the gate cannot prevent
it, because a direct push to `develop` is not a pull request. The release branch keeps the bump off
`develop` until `main` has advanced; the back-merge then carries it over. `develop` keeps receiving
work while a release is under review: the release ships what `develop` held when the branch was cut,
and later merges ride the next one.

## The version

`plugin/.claude-plugin/plugin.json` is the single source of truth. Neither marketplace manifest
declares a version: Claude Code resolves the version `plugin.json` → marketplace entry → git commit
SHA, so a marketplace copy is silently outranked and only creates a drift class. The gate rejects a
marketplace manifest that declares one.

Removing the version from `plugin.json` as well is not an option — that flips the plugin into
per-commit versioning, where every new commit is treated as a new version. This project releases
deliberately, so the explicit SemVer stays.

## Cutting a release

1. Cut the release branch from the current `develop` without inheriting its upstream:
   `git fetch origin && git switch -c release/X.Y.Z --no-track origin/develop`. The `--no-track`
   matters: a release branch that tracks `develop` turns a bare `git push` into a push of the bump
   onto `develop` under `push.default=upstream` — the one thing this procedure exists to prevent.
2. On that branch, and only there, raise the version in `plugin/.claude-plugin/plugin.json`.
3. Run `./build-plugin.sh`. The bump itself produces no build output — the marketplace manifests
   carry no version — so the build is a drift check: `git status` must show no change afterwards. If a
   tracked file moved, something had drifted — the committed `plugin/` tree from its sources
   (`.claude/`, `plugin-extras/`, `tools/`), or the generated agent-router from the current agent
   set — and that drift is fixed on `develop` first, not on the release branch.
   Never hand-edit the generated `plugin/` tree. The exceptions the build preserves are
   `plugin/.claude-plugin/` — both manifests; the root `.claude-plugin/marketplace.json` is generated
   *from* `plugin/.claude-plugin/marketplace.json` — and `plugin/README.md`.
4. Update the documentation surfaces the gate checks — the `README.md` version badge, the
   `CLAUDE.md` status line and version block, and the `SECURITY.md` supported-versions table, which is
   keyed to `X.Y.x` and therefore changes only on a minor or major release.
5. Consolidate `CHANGELOG.md`: rename `## [Unreleased]` to `## [X.Y.Z] - <date>`, dated the day the
   release is cut, fill in whatever the merged pull requests did not record, and leave a fresh, empty
   `## [Unreleased]` above it.
6. Push the branch, naming it explicitly — `git push -u origin release/X.Y.Z` — and open the release
   PR from `release/X.Y.Z` into `main`, with the release template (`?template=release.md`). Its body
   is the release report: the pull requests merged into `develop` since the previous release and the
   issues they close, what is deliberately left out, and the test plan. The gate runs in its `main`
   mode — the version must be strictly greater than `main`'s. This is also the first pull request in
   the cycle on which `Validate Plugin` and `Quality Checks` run at all — both are scoped to
   `main`-base pull requests — so expect them to surface anything `develop` accumulated since the
   last release.
7. Merge the release PR with a **merge commit**, never a squash. A squash collapses the commits
   `develop` already carries into one new commit, so the release's commits never become ancestors of
   `main`: the back-merge then reconciles two different commits with the same content, and `main`'s
   history no longer shows the individual changes the tag points at. Unless the repository restricts
   merge methods, nothing but this rule enforces it; restricting `main` to merge commits is a
   repository setting.
8. Immediately merge `main` back into `develop`, through a branch — a PR whose head is `main` offers
   no place to correct anything: `git fetch origin && git switch -c chore/back-merge-X.Y.Z --no-track
   origin/develop && git merge origin/main`, then push it (`git push -u origin chore/back-merge-X.Y.Z`)
   and open that branch into `develop`, merging it with a merge commit. It
   carries the bump, the documentation surfaces and the changelog consolidation — plus anything
   `main` gained from a hotfix — and it restores the equality the `develop` gate checks; it passes
   that gate by construction, since its version is `main`'s. Between the release merge and this
   back-merge, any pull request against `develop` that is re-evaluated fails the gate — its version
   is one behind `main`'s — which is why the back-merge is part of the same procedure and not a later
   chore. `CHANGELOG.md` needs a manual pass in that merge whenever `develop` gained `[Unreleased]`
   entries after the cut: git may report a conflict, or — worse — merge cleanly and file those
   entries inside the release's `## [X.Y.Z]` section. Either way, every entry added after the cut
   goes back under `## [Unreleased]`, and `## [X.Y.Z]` ends up identical to `main`'s. No other file
   should need attention.
9. Create an annotated tag on the release merge commit (`git tag -a vX.Y.Z <sha>`) and push it, then
   publish the GitHub Release from that tag. Delete `release/X.Y.Z`.

A release that goes stale under review ships what it holds; the next release picks up the rest. If it
must absorb newer work instead, merge `develop` into the release branch, redo step 5 for what was
absorbed — otherwise its changelog entries stay under `[Unreleased]` and ship undocumented — and
push. The reviewed artifact changed, so review starts over.

Point-in-time artifacts — presentation decks, past release notes — are deliberately excluded from
the surface check. Retro-editing them would misrepresent what was presented at the time.

## Hotfixes

A fix that cannot wait for the next release may target `main` directly. A hotfix PR is checked in
the gate's `main` mode, so if it touches `plugin/` or `.claude-plugin/` it carries its own patch
bump plus steps 3–4 above and a new `## [X.Y.Z]` section in `CHANGELOG.md` (`main`'s `[Unreleased]`
is empty after a release, so there is nothing to rename). Merge `main` back into `develop`
immediately afterwards, exactly as after a release; that back-merge passes the `develop` gate by
construction. Skipping the back-merge leaves `develop` behind `main`, and the next release will
silently revert the hotfix.

## What the gate enforces

`scripts/bump.sh --check` runs in CI on every pull request against `main` or `develop`, comparing
against `origin/main` in both modes.

| PR base | Rule |
|---|---|
| `main` | If anything under `plugin/` or `.claude-plugin/` changed, the version must be **strictly greater** than `main`'s. An unchanged shipped tree is a no-op. Release PRs and hotfix PRs are both checked this way. |
| `develop` | The version must **equal** `main`'s. `develop` never carries a bump; the release branch is what advances it, and back-merging `main` afterwards restores equality. The back-merge branch passes by construction — its version *is* `main`'s. |

Independently of the mode, the gate asserts that all three manifests are consistent — `plugin.json`
carries a valid `X.Y.Z`, and neither marketplace manifest declares a version at all. When the PR
contains a shipped change, it additionally asserts that every documentation surface states that same
version and that `CHANGELOG.md` has a matching section.

Only plain `X.Y.Z` is accepted. Leading zeros and pre-release or build suffixes are rejected.

Adding a new surface to the check is a single row in `_surface_rows` in `scripts/bump.sh`.

### Waiver

Setting `HAS_NO_RELEASE=true` skips the gate entirely. The calling workflow wires it from a
`no-release` PR label. The label does not exist on the board yet, so the waiver is dormant.

### A race worth knowing about

The gate runs when a PR is created and again on push, but not necessarily at the moment of merge. If
two PRs targeting `main` are open at once and the first merges a version bump, the second can carry
a stale comparison. Enabling *Require branches to be up to date before merging* on `main` closes it,
by forcing the second PR to rebase — which re-runs the gate against the new base. That is a
repository setting, not something this script can enforce.

### What the gate cannot see

The gate is a pull-request check. A commit pushed directly to `develop` or `main` never meets it, and
a version raised that way on `develop` fails every open pull request against `develop` at once.
Requiring a pull request for both branches — a repository ruleset — is what closes that gap, provided
no bypass actor is granted on it: an administrator with bypass can still push directly. Like the
up-to-date rule above, it is a repository setting, not something this script can enforce.
