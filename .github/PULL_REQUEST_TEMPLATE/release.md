# Release PR

*Opt-in template for a `release/X.Y.Z` → `main` release PR — apply it explicitly with `?template=release.md`, since directory-form templates are not auto-applied. Feature and fix PRs are unaffected.*

The authority for this procedure is [`docs/reference/releasing.md`](../../docs/reference/releasing.md).
This checklist points at it; it does not restate it.

## Release

| | |
|---|---|
| Version          | `X.Y.Z` |
| Previous version | `X.Y.Z` |
| Cut from `develop` at | `<sha>` |

### What's in it

- #<PR> — <one line>. Closes #<issue>

### Not in this release

- #<PR> — <why it waits>

## Before merge

- [ ] Branch is `release/X.Y.Z`, cut from `develop`; the version was not touched on `develop`
- [ ] `plugin/.claude-plugin/plugin.json` version raised on this branch
- [ ] `./build-plugin.sh` run — root `.claude-plugin/marketplace.json` regenerated, nothing else changed
- [ ] Doc surfaces updated — `README.md` badge, `CLAUDE.md` status + version block, `SECURITY.md` supported-versions table
- [ ] `CHANGELOG.md` — `[Unreleased]` consolidated into `## [X.Y.Z] - <date>`, dated the day the release is cut; fresh empty `[Unreleased]` above it
- [ ] `bump-gate` CI check green (locally: `GITHUB_BASE_REF=main bash scripts/bump.sh --check`)

## Merge

- [ ] Merge commit — never squash

## After merge

- [ ] Back-merge PR `main` → `develop` opened and merged immediately (merge commit); `bump-gate` green on it
- [ ] Annotated tag `vX.Y.Z` created on the merge commit and pushed; GitHub Release published from it
- [ ] `release/X.Y.Z` deleted
