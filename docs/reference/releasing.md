# Releasing

Maintainer procedure for cutting a release. Contributors do not need this document — see
[`CONTRIBUTING.md`](../../CONTRIBUTING.md), which covers everything required to open a pull request.

## Branch topology

| Branch | Role |
|---|---|
| `develop` | Integration branch. All feature, fix and documentation work lands here. Its version always equals `main`'s. |
| `main` | Released code. It receives release PRs from `develop`, and hotfixes. Every commit on it is a candidate release point. |

`develop` was cut from the `v3.5.0` tag. A tag is created for every release and never moved.

## The version

`plugin/.claude-plugin/plugin.json` is the single source of truth. Neither marketplace manifest
declares a version: Claude Code resolves the version `plugin.json` → marketplace entry → git commit
SHA, so a marketplace copy is silently outranked and only creates a drift class. The gate rejects a
marketplace manifest that declares one.

Removing the version from `plugin.json` as well is not an option — that flips the plugin into
per-commit versioning, where every new commit is treated as a new version. This project releases
deliberately, so the explicit SemVer stays.

## Cutting a release

1. Open a release PR from `develop` into `main`.
2. In that PR, and only there, raise the version in `plugin/.claude-plugin/plugin.json`.
3. Run `./build-plugin.sh` to regenerate the root `.claude-plugin/marketplace.json`. Never hand-edit
   the generated file.
4. Update the documentation surfaces the gate checks — the `README.md` version badge, the
   `CLAUDE.md` status line and version block, and the `SECURITY.md` supported-versions table — and
   add a `## [X.Y.Z]` section to `CHANGELOG.md` dated the day the release is actually cut.
5. Merge the release PR into `main`.
6. Create an annotated tag on the merge commit (`git tag -a vX.Y.Z <sha>`) and push it, then publish
   the GitHub Release from that tag.

Point-in-time artifacts — presentation decks, past release notes — are deliberately excluded from
the surface check. Retro-editing them would misrepresent what was presented at the time.

## Hotfixes

A fix that cannot wait for the next release may target `main` directly. Merge `main` back into
`develop` immediately afterwards. Skipping the back-merge leaves `develop` behind `main`, and the
next release PR will silently revert the hotfix.

## What the gate enforces

`scripts/bump.sh --check` runs in CI on every pull request, against `origin/main` in both modes.

| PR base | Rule |
|---|---|
| `main` | If anything under `plugin/` or `.claude-plugin/` changed, the version must be **strictly greater** than `main`'s. An unchanged shipped tree is a no-op. |
| `develop` | The version must **equal** `main`'s. `develop` never carries a bump; the release PR is what advances it, and back-merging `main` afterwards restores equality. |

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
