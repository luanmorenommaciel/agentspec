# Release PR

*Opt-in template for a `develop` → `main` release — apply it explicitly with
`?template=release.md`, since directory-form templates are not auto-applied. Feature
and fix PRs are unaffected.*

The authority for this procedure is [`docs/reference/releasing.md`](../../docs/reference/releasing.md).
This checklist points at it; it does not restate it.

## Release

| | |
|---|---|
| Version          | `X.Y.Z` |
| Previous version | `X.Y.Z` |

### What's in it

- Closes #

### Not in this release

-

## Before merge

- [ ] `plugin/.claude-plugin/plugin.json` version bumped
- [ ] `./build-plugin.sh` run — root `.claude-plugin/marketplace.json` regenerated
- [ ] Doc surfaces updated — `README.md` badge, `CLAUDE.md` status + version block, `SECURITY.md` supported-versions table
- [ ] `CHANGELOG.md` section added
- [ ] `bump-gate` CI check green (locally: `GITHUB_BASE_REF=main bash scripts/bump.sh --check`)

## After merge

- [ ] Annotated tag `vX.Y.Z` created on the merge commit and pushed; GitHub Release published from it
