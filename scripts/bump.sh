#!/usr/bin/env bash
# scripts/bump.sh — release-readiness version-bump gate.
#
#   scripts/bump.sh --check [--base-ref <branch>]
#
# --check ONLY. There is no --apply: in this repo, version bumps are applied
# by hand as part of the release PR (edit the "version" in
# plugin/.claude-plugin/plugin.json — the single source of truth — then run
# ./build-plugin.sh to resync the generated root .claude-plugin/marketplace.json).
# No automated executor writes the version today; if one is added later, give
# it its own flag rather than repurposing this file's read-only contract.
#
# Doctrine — dual mode by PR base (GITHUB_BASE_REF on a pull_request event):
#   base=main:    "shipped" (plugin/ + .claude-plugin/) changed vs origin/main
#                 -> version must be STRICTLY GREATER than origin/main's.
#                 unchanged -> no-op, always OK.
#   base=develop: version must EQUAL origin/main's version. develop never
#                 carries a bump itself — a release PR (develop -> main) is
#                 what advances the version, and back-merging main into
#                 develop afterwards self-heals the equality.
# Both modes compare against origin/main ONLY. --base-ref selects which
# doctrine applies; it is not a ref this script diffs against (origin/develop
# is never fetched or read).
#
# When a PR carries a shipped change, the gate additionally asserts that every
# living documentation surface (README badge, CLAUDE.md status + version block,
# SECURITY.md supported-versions table) states the same version, and that
# CHANGELOG.md carries a section for it.
#
# Waiver: HAS_NO_RELEASE=true (wired from the `no-release` PR label by the
# calling workflow) skips the gate entirely. Dormant today — the label does
# not exist on the board yet.
set -euo pipefail

readonly PLUGIN_JSON="plugin/.claude-plugin/plugin.json"
readonly PLUGIN_MARKETPLACE_JSON="plugin/.claude-plugin/marketplace.json"
readonly ROOT_MARKETPLACE_JSON=".claude-plugin/marketplace.json"
readonly SHIPPED_PATHS=(plugin/ .claude-plugin/)
readonly BASE_REMOTE_REF="origin/main"

die() { echo "bump: $*" >&2; exit 1; }

usage() { die "usage: bump.sh --check [--base-ref <branch>]"; }

# --- version IO (python3: robust read of the two manifest shapes) ---
_plugin_json_version() {  # <path> — top-level "version"
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$1"
}
_marketplace_declares_version() {  # <path> — exit 0 if plugins[0] carries a "version" key
  python3 -c 'import json,sys; sys.exit(0 if "version" in json.load(open(sys.argv[1]))["plugins"][0] else 1)' "$1"
}
_plugin_json_version_at() {  # <git-ref> — plugin.json's "version" as of that ref
  git show "${1}:${PLUGIN_JSON}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["version"])'
}

# --- semver (pure bash, portable) ---
require_semver() {  # accept only plain X.Y.Z integers — no leading zeros, no pre-release/build suffixes
  printf '%s' "$1" | grep -Eq '^(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*)){2}$' \
    || die "version '$1' is not plain X.Y.Z (leading zeros and pre-release/build suffixes unsupported)"
}
semver_gt() {  # "is A > B ?" -> exit 0 if yes
  local aM aN aP bM bN bP
  IFS=. read -r aM aN aP <<<"$1"
  IFS=. read -r bM bN bP <<<"$2"
  [ "$aM" -gt "$bM" ] && return 0; [ "$aM" -lt "$bM" ] && return 1
  [ "$aN" -gt "$bN" ] && return 0; [ "$aN" -lt "$bN" ] && return 1
  [ "$aP" -gt "$bP" ]
}

ensure_base() {
  git fetch -q origin "main:refs/remotes/origin/main" 2>/dev/null \
    || git fetch -q origin main 2>/dev/null || true
  git rev-parse --verify -q "${BASE_REMOTE_REF}" >/dev/null \
    || die "cannot resolve ${BASE_REMOTE_REF} (fetch failed?)"
}

shipped_changed() { ! git diff --quiet "${BASE_REMOTE_REF}" -- "${SHIPPED_PATHS[@]}"; }

# plugin.json is the single source of truth for the version. The marketplace
# manifests must NOT carry one: Claude Code resolves plugin.json -> marketplace
# entry -> git SHA, so a marketplace "version" is silently outranked and only
# creates a drift class. This gate keeps the duplicate from coming back.
check_manifest_version() {
  [ -f "$PLUGIN_JSON" ] || die "missing $PLUGIN_JSON — run from the repo root"
  [ -f "$PLUGIN_MARKETPLACE_JSON" ] || die "missing $PLUGIN_MARKETPLACE_JSON — run from the repo root"
  [ -f "$ROOT_MARKETPLACE_JSON" ] || die "missing $ROOT_MARKETPLACE_JSON — run from the repo root"

  local canonical
  canonical="$(_plugin_json_version "$PLUGIN_JSON")"
  require_semver "$canonical"

  local offenders=() m
  for m in "$PLUGIN_MARKETPLACE_JSON" "$ROOT_MARKETPLACE_JSON"; do
    if _marketplace_declares_version "$m"; then offenders+=("$m"); fi
  done

  if [ "${#offenders[@]}" -gt 0 ]; then
    local joined
    joined="$(printf ', %s' "${offenders[@]}")"
    die "marketplace manifest must not declare a version (${joined:2})" \
      "— $PLUGIN_JSON is the single source of truth; drop the field and run ./build-plugin.sh"
  fi

  printf '%s' "$canonical"
}

# --- documentation version surfaces ---
# Every living document that states the shipped version. Adding a surface is one
# row: <path> TAB <python regex with one capture group> TAB <mode> TAB <expected>.
# mode=first   the first capture must equal <expected>
# mode=present some capture must equal <expected>
# Point-in-time artifacts (decks, past release notes) are deliberately excluded —
# retro-editing them would misrepresent what was presented at the time.
_surface_rows() {  # <version>
  local v="$1" minor="${1%.*}"
  printf '%s\t%s\t%s\t%s\n' \
    "README.md" '!\[Version\]\(https://img\.shields\.io/badge/v([0-9]+\.[0-9]+\.[0-9]+)-' "first" "$v"
  printf '%s\t%s\t%s\t%s\n' \
    "CLAUDE.md" '\*\*Current Status:\*\* v([0-9]+\.[0-9]+\.[0-9]+)' "first" "$v"
  printf '%s\t%s\t%s\t%s\n' \
    "CLAUDE.md" '^- \*\*Version:\*\* ([0-9]+\.[0-9]+\.[0-9]+)' "first" "$v"
  printf '%s\t%s\t%s\t%s\n' \
    "SECURITY.md" '^\| *([0-9]+\.[0-9]+)\.x *\| *Yes' "first" "$minor"
  printf '%s\t%s\t%s\t%s\n' \
    "CHANGELOG.md" '^## \[([0-9]+\.[0-9]+\.[0-9]+)\]' "present" "$v"
}

_check_surface() {  # <path> <regex> <mode> <expected> — prints a reason on failure
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import pathlib, re, sys
path, pattern, mode, expected = sys.argv[1:5]
p = pathlib.Path(path)
if not p.exists():
    print(f"{path}: not found"); sys.exit(1)
found = re.findall(pattern, p.read_text(encoding="utf-8"), flags=re.M)
if not found:
    print(f"{path}: no version string matched (expected {expected})"); sys.exit(1)
if mode == "present":
    if expected not in found:
        print(f"{path}: no entry for {expected} (has {', '.join(found[:4])})"); sys.exit(1)
elif found[0] != expected:
    print(f"{path}: states {found[0]}, expected {expected}"); sys.exit(1)
PY
}

# The manifests decide what ships; these documents announce it. A release whose
# README still advertises the previous version undercuts the release itself, so
# the gate treats an out-of-date surface as a failure rather than a cosmetic lag.
check_doc_surfaces() {  # <canonical-version>
  local failures=() path pattern mode expected reason
  while IFS=$'\t' read -r path pattern mode expected; do
    if ! reason="$(_check_surface "$path" "$pattern" "$mode" "$expected")"; then
      failures+=("$reason")
    fi
  done < <(_surface_rows "$1")

  if [ "${#failures[@]}" -gt 0 ]; then
    local joined
    joined="$(printf '; %s' "${failures[@]}")"
    die "version surfaces out of date — ${joined:2}"
  fi
  echo "bump: version surfaces agree with $1 (README, CLAUDE.md, SECURITY.md, CHANGELOG)"
}

check_main_mode() {  # <current-version>
  local cur="$1" base
  if ! shipped_changed; then
    echo "bump: no shipped (plugin/, .claude-plugin/) change vs origin/main — OK"
    return 0
  fi
  base="$(_plugin_json_version_at "${BASE_REMOTE_REF}")"
  require_semver "$base"
  if semver_gt "$cur" "$base"; then
    echo "bump: shipped change vs origin/main; version $cur > $base — OK"
    return 0
  fi
  die "shipped (plugin/, .claude-plugin/) changed but version $cur is not > origin/main's $base" \
    "— bump plugin/.claude-plugin/plugin.json, then run ./build-plugin.sh"
}

check_develop_mode() {  # <current-version>
  local cur="$1" base
  base="$(_plugin_json_version_at "${BASE_REMOTE_REF}")"
  require_semver "$base"
  if [ "$cur" = "$base" ]; then
    echo "bump: develop base; version $cur == origin/main's $base — OK"
    return 0
  fi
  die "develop never carries a version bump — version $cur must equal origin/main's $base" \
    "(a release PR, develop -> main, is what advances the version; back-merge main into develop to self-heal)"
}

main() {
  local mode="" base_ref=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --check) mode="check"; shift ;;
      --base-ref)
        [ "$#" -ge 2 ] && [ -n "$2" ] || die "--base-ref requires a value"
        base_ref="$2"; shift 2 ;;
      *) usage ;;
    esac
  done
  [ "$mode" = "check" ] || usage

  if [ "${HAS_NO_RELEASE:-}" = "true" ]; then
    echo "bump: 'no-release' label present — version-bump gate waived."
    exit 0
  fi

  [ -n "$base_ref" ] || base_ref="${GITHUB_BASE_REF:-main}"

  ensure_base
  local cur
  cur="$(check_manifest_version)"

  case "$base_ref" in
    main) check_main_mode "$cur" ;;
    develop) check_develop_mode "$cur" ;;
    *) die "unsupported --base-ref '$base_ref' (only main|develop are recognized)" ;;
  esac

  # Documentation surfaces are only asserted when this PR actually ships something.
  # A docs-only or tooling-only PR is not the place to discover pre-existing drift.
  if shipped_changed; then
    check_doc_surfaces "$cur"
  else
    echo "bump: no shipped change — version surfaces not checked"
  fi
}
main "$@"
