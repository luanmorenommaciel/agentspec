#!/usr/bin/env bash
# =============================================================================
# rollout-agentspec.sh — upgrade vendored AgentSpec installs in consuming repos
#
# Consuming repos vendor AgentSpec inside their .claude/ directory (no plugin
# install). This script updates the AgentSpec-owned payload in each target
# WITHOUT touching the target's own work:
#
#   NEVER TOUCHED (preserved by construction — the script only writes into
#   the managed paths listed below):
#     .claude/sdd/features/  .claude/sdd/reports/  .claude/sdd/archive/
#     .claude/sdd/drafts/    .claude/settings*.json  .claude/scheduled_tasks.lock
#     .claude/agent-memory/  .claude/storage/  .claude/hooks/  .claude/dev/
#     target-only KB domains, skills, command dirs/files, agent dirs
#
#   REPLACED (delete-then-copy, scoped to AgentSpec-owned names only):
#     agents/{architect,cloud,platform,python,test,data-engineering,dev,workflow}
#     commands/{workflow,data-engineering,core,knowledge,review,visual-explainer}
#     skills/<each skill shipped in the plugin payload>
#     kb/<each domain shipped in the plugin payload> + kb/_templates
#     sdd/templates/  sdd/architecture/  tools/spec-linter/  tools/spec-judge/
#     scripts/judge.py  scripts/autopilot.sh  + the managed README/_index files
#
#   MERGED:
#     kb/_index.yaml — new payload index + the target's target-only domain
#     entries appended (validated; on any failure the target's old index is
#     kept and the skip is reported loudly)
#
# The payload is staged from plugin/ (the canonical built artifact — run
# `make build` first or pass --build) and path-rewritten for vendored use:
# ${CLAUDE_PLUGIN_ROOT} → ${CLAUDE_PLUGIN_ROOT:-.claude}.
#
# Usage:
#   scripts/rollout-agentspec.sh                       # dry-run, targets from file
#   scripts/rollout-agentspec.sh --apply               # write, with backups
#   scripts/rollout-agentspec.sh --apply ~/x/repo      # explicit targets
#   scripts/rollout-agentspec.sh --rollback --stamp S  # restore from backup
#
# Options:
#   --apply          Write changes (default is a read-only dry-run plan)
#   --build          Run `make build` in the source repo before staging
#   --source DIR     AgentSpec repo root (default: this script's repo)
#   --stamp STAMP    Backup stamp (default: current YYYYmmdd-HHMMSS)
#   --rollback       Restore each target's .claude from the --stamp backup
#   --help           Show this help
#
# Targets: pass directories as arguments, or list them in
# .agentspec-rollout-targets at the repo root (gitignored) — one path per
# line, '#' comments allowed; override the file with $AGENTSPEC_ROLLOUT_TARGETS.
#
# Backups: ~/.agentspec-rollout-backups/<stamp>/<target-name>/.claude
# Exit codes: 0 success · 1 partial (a target failed/skipped) · 2 bad usage/env
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_ROOT="${HOME}/.agentspec-rollout-backups"

MODE="dry-run"
DO_BUILD=0
ROLLBACK=0
STAMP="$(date +%Y%m%d-%H%M%S)"
STAMP_GIVEN=0
TARGETS=()
STAGE=""
FAILURES=0

TARGETS_FILE="${AGENTSPEC_ROLLOUT_TARGETS:-${SOURCE_DIR}/.agentspec-rollout-targets}"

AGENT_CATEGORIES=(architect cloud platform python test data-engineering dev workflow)
COMMAND_SETS=(workflow data-engineering core knowledge review visual-explainer)
SDD_SETS=(templates architecture)
TOOL_SETS=(spec-linter spec-judge)
SCRIPT_FILES=(judge.py autopilot.sh)

log()  { printf '%s\n' "$*"; }
info() { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 2; }

usage() { sed -n '2,54p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --apply)    MODE="apply" ;;
            --build)    DO_BUILD=1 ;;
            --rollback) ROLLBACK=1 ;;
            --source)   shift; SOURCE_DIR="${1:?--source needs a value}" ;;
            --stamp)    shift; STAMP="${1:?--stamp needs a value}"; STAMP_GIVEN=1 ;;
            --help|-h)  usage; exit 0 ;;
            -*)         die "unknown option: $1 (see --help)" ;;
            *)          TARGETS+=("$1") ;;
        esac
        shift
    done
    if [[ ${#TARGETS[@]} -eq 0 && -f "$TARGETS_FILE" ]]; then
        local line
        while IFS= read -r line; do
            line="${line%%#*}"
            line="${line#"${line%%[![:space:]]*}"}"
            line="${line%"${line##*[![:space:]]}"}"
            [[ -n "$line" ]] && TARGETS+=("${line/#\~\//${HOME}/}")
        done < "$TARGETS_FILE"
    fi
    if [[ ${#TARGETS[@]} -eq 0 ]]; then
        die "no targets: pass target directories or list them in ${TARGETS_FILE}"
    fi
}

require_python() {
    command -v python3 >/dev/null 2>&1 || die "python3 is required (kb index merge + path rewrite)"
    python3 -c 'import yaml' 2>/dev/null || die "python3 'yaml' module is required (pip install pyyaml)"
}

# --- staging ----------------------------------------------------------------

stage_payload() {
    local plugin_dir="${SOURCE_DIR}/plugin"
    [[ -f "${plugin_dir}/.claude-plugin/plugin.json" ]] \
        || die "no built payload at ${plugin_dir} — run 'make build' in ${SOURCE_DIR} or pass --build"

    if [[ "$DO_BUILD" -eq 1 ]]; then
        info "Building payload (make build in ${SOURCE_DIR})"
        make -C "$SOURCE_DIR" build >/dev/null || die "make build failed"
    fi

    local version
    version="$(python3 -c "import json;print(json.load(open('${plugin_dir}/.claude-plugin/plugin.json'))['version'])" 2>/dev/null || echo "unknown")"
    info "Payload: ${plugin_dir} (version ${version})"

    STAGE="$(mktemp -d "${TMPDIR:-/tmp}/agentspec-rollout.XXXXXX")"
    trap 'rm -rf "$STAGE"' EXIT

    cp -R "${plugin_dir}/agents"   "${STAGE}/agents"
    cp -R "${plugin_dir}/commands" "${STAGE}/commands"
    cp -R "${plugin_dir}/skills"   "${STAGE}/skills"
    cp -R "${plugin_dir}/kb"       "${STAGE}/kb"
    cp -R "${plugin_dir}/sdd"      "${STAGE}/sdd"
    cp -R "${plugin_dir}/tools"    "${STAGE}/tools"

    mkdir -p "${STAGE}/scripts"
    cp "${SOURCE_DIR}/scripts/judge.py" "${STAGE}/scripts/judge.py"
    cp "${plugin_dir}/scripts/autopilot.sh" "${STAGE}/scripts/autopilot.sh"
    chmod +x "${STAGE}/scripts/autopilot.sh"

    rewrite_paths_for_vendored
    info "Staged and path-rewritten for vendored installs (\${CLAUDE_PLUGIN_ROOT:-.claude})"
}

rewrite_paths_for_vendored() {
    STAGE="$STAGE" python3 - <<'PYEOF'
import os, pathlib

stage = pathlib.Path(os.environ["STAGE"])
exts = {".md", ".yaml", ".yml", ".py", ".sh", ".json", ".txt"}
old_defaulted = "${CLAUDE_PLUGIN_ROOT:-.}"
old_bare = "${CLAUDE_PLUGIN_ROOT}"
new = "${CLAUDE_PLUGIN_ROOT:-.claude}"

changed = 0
for path in stage.rglob("*"):
    if not path.is_file() or path.suffix not in exts:
        continue
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    replaced = text.replace(old_defaulted, new).replace(old_bare, new)
    if replaced != text:
        path.write_text(replaced, encoding="utf-8", errors="surrogateescape")
        changed += 1
print(f"    path-rewrite: {changed} files updated")
PYEOF
}

# --- helpers ----------------------------------------------------------------

replace_path() {
    local src="$1" dst="$2"
    if [[ "$MODE" == "apply" ]]; then
        rm -rf "$dst"
        mkdir -p "$(dirname "$dst")"
        cp -R "$src" "$dst"
    fi
}

list_dirs() {
    local parent="$1"
    [[ -d "$parent" ]] || return 0
    find "$parent" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort
}

contains() {
    local needle="$1"; shift
    local item
    for item in "$@"; do [[ "$item" == "$needle" ]] && return 0; done
    return 1
}

# --- kb index merge ---------------------------------------------------------

merge_kb_index() {
    local target_claude="$1" report_only="$2"
    NEW_INDEX="${STAGE}/kb/_index.yaml" \
    OLD_INDEX="${target_claude}/kb/_index.yaml" \
    REPORT_ONLY="$report_only" python3 - <<'PYEOF'
import os, sys, yaml

new_path = os.environ["NEW_INDEX"]
old_path = os.environ["OLD_INDEX"]
report_only = os.environ["REPORT_ONLY"] == "1"

try:
    new_doc = yaml.safe_load(open(new_path))
    old_doc = yaml.safe_load(open(old_path)) if os.path.exists(old_path) else {}
    new_domains = new_doc.get("domains") or {}
    old_domains = (old_doc or {}).get("domains") or {}
    missing = {k: v for k, v in old_domains.items() if k not in new_domains}
except Exception as exc:
    print(f"    kb/_index.yaml: MERGE SKIPPED ({exc}) — keeping the target's existing index", file=sys.stderr)
    sys.exit(3)

if not missing:
    print("    kb/_index.yaml: no target-only domains — payload index used as-is")
    sys.exit(0)

names = ", ".join(sorted(missing))
if report_only:
    print(f"    kb/_index.yaml: would merge {len(missing)} target-only domains: {names}")
    sys.exit(0)

block = yaml.safe_dump(missing, default_flow_style=False, sort_keys=True, allow_unicode=True)
indented = "".join("  " + line + "\n" for line in block.splitlines())
merged_text = (
    open(new_path).read().rstrip("\n")
    + "\n\n  # --- target-only domains (preserved by rollout-agentspec.sh) ---\n"
    + indented
)

parsed = yaml.safe_load(merged_text)
merged_domains = parsed.get("domains") or {}
expected = set(new_domains) | set(missing)
if set(merged_domains) != expected:
    print("    kb/_index.yaml: MERGE VALIDATION FAILED — keeping the target's existing index", file=sys.stderr)
    sys.exit(3)

with open(os.environ["OLD_INDEX"], "w") as fh:
    fh.write(merged_text)
print(f"    kb/_index.yaml: merged {len(missing)} target-only domains: {names}")
PYEOF
}

# --- per-target -------------------------------------------------------------

report_preserved() {
    local tc="$1"
    local extra_kb extra_skills extra_cmds
    extra_kb="$(comm -13 <(list_dirs "${STAGE}/kb") <(list_dirs "${tc}/kb") | tr '\n' ' ')"
    extra_skills="$(comm -13 <(list_dirs "${STAGE}/skills") <(list_dirs "${tc}/skills") | tr '\n' ' ')"
    extra_cmds="$(comm -13 <(list_dirs "${STAGE}/commands") <(list_dirs "${tc}/commands") | tr '\n' ' ')"
    log "    preserved (target-owned): sdd/{features,reports,archive$( [[ -d "${tc}/sdd/drafts" ]] && printf ',drafts')}, settings*, agent-memory/, dev/"
    [[ -n "${extra_kb// /}" ]]     && log "    preserved kb domains: ${extra_kb}"
    [[ -n "${extra_skills// /}" ]] && log "    preserved skills: ${extra_skills}"
    [[ -n "${extra_cmds// /}" ]]   && log "    preserved command dirs: ${extra_cmds}"
    return 0
}

report_unclassified() {
    local tc="$1" entry base
    local known=(agents commands kb skills sdd tools scripts dev hooks agent-memory storage)
    for entry in "$tc"/* "$tc"/.[!.]*; do
        [[ -e "$entry" ]] || continue
        base="$(basename "$entry")"
        case "$base" in
            settings*.json|scheduled_tasks.lock|.DS_Store|.gitignore) continue ;;
        esac
        contains "$base" "${known[@]}" || log "    UNCLASSIFIED (preserved, review manually): ${base}"
    done
    return 0
}

backup_target() {
    local target="$1" name="$2"
    local dest="${BACKUP_ROOT}/${STAMP}/${name}"
    mkdir -p "$dest"
    cp -R "${target}/.claude" "${dest}/.claude"
    log "    backup: ${dest}/.claude"
}

sync_target() {
    local target="$1"
    local name tc item
    name="$(basename "$target")"
    tc="${target}/.claude"

    log ""
    info "Target: ${target} [${MODE}]"

    if [[ ! -d "$tc" ]]; then
        warn "no .claude directory — skipping ${name}"
        FAILURES=$((FAILURES + 1))
        return 0
    fi

    [[ "$MODE" == "apply" ]] && backup_target "$target" "$name"

    for item in "${AGENT_CATEGORIES[@]}"; do
        [[ -d "${STAGE}/agents/${item}" ]] && replace_path "${STAGE}/agents/${item}" "${tc}/agents/${item}"
    done
    replace_path "${STAGE}/agents/README.md" "${tc}/agents/README.md"
    log "    agents: replaced ${#AGENT_CATEGORIES[@]} categories + README"

    for item in "${COMMAND_SETS[@]}"; do
        [[ -d "${STAGE}/commands/${item}" ]] && replace_path "${STAGE}/commands/${item}" "${tc}/commands/${item}"
    done
    [[ -f "${STAGE}/commands/README.md" ]] && replace_path "${STAGE}/commands/README.md" "${tc}/commands/README.md"
    log "    commands: replaced ${#COMMAND_SETS[@]} AgentSpec dirs + README"

    local skill_count=0
    while IFS= read -r item; do
        replace_path "${STAGE}/skills/${item}" "${tc}/skills/${item}"
        skill_count=$((skill_count + 1))
    done < <(list_dirs "${STAGE}/skills")
    log "    skills: replaced ${skill_count} distributed skills"

    local kb_count=0
    while IFS= read -r item; do
        replace_path "${STAGE}/kb/${item}" "${tc}/kb/${item}"
        kb_count=$((kb_count + 1))
    done < <(list_dirs "${STAGE}/kb")
    [[ -f "${STAGE}/kb/README.md" ]] && replace_path "${STAGE}/kb/README.md" "${tc}/kb/README.md"
    log "    kb: replaced ${kb_count} payload domains (incl. _templates, shared)"

    if [[ "$MODE" == "apply" ]]; then
        cp "${STAGE}/kb/_index.yaml" "${tc}/kb/_index.yaml.rollout-new"
        mv "${tc}/kb/_index.yaml" "${tc}/kb/_index.yaml.rollout-old" 2>/dev/null || true
        mv "${tc}/kb/_index.yaml.rollout-new" "${tc}/kb/_index.yaml"
        OLD_KEPT="${tc}/kb/_index.yaml.rollout-old"
        if OLD_INDEX_FOR_MERGE="$OLD_KEPT" merge_kb_index_apply "$tc"; then
            rm -f "$OLD_KEPT"
        else
            mv "$OLD_KEPT" "${tc}/kb/_index.yaml" 2>/dev/null \
                || warn "no previous kb/_index.yaml to restore for ${name}"
            warn "kb/_index.yaml merge failed for ${name} — old index kept (new domains unregistered until fixed)"
        fi
    else
        merge_kb_index "$tc" "1" || true
    fi

    for item in "${SDD_SETS[@]}"; do
        replace_path "${STAGE}/sdd/${item}" "${tc}/sdd/${item}"
    done
    for item in README.md _index.md; do
        [[ -f "${STAGE}/sdd/${item}" ]] && replace_path "${STAGE}/sdd/${item}" "${tc}/sdd/${item}"
    done
    log "    sdd: replaced templates/, architecture/ + index docs (features/reports/archive untouched)"

    for item in "${TOOL_SETS[@]}"; do
        [[ -d "${STAGE}/tools/${item}" ]] && replace_path "${STAGE}/tools/${item}" "${tc}/tools/${item}"
    done
    log "    tools: replaced spec-linter, spec-judge"

    for item in "${SCRIPT_FILES[@]}"; do
        [[ -f "${STAGE}/scripts/${item}" ]] && replace_path "${STAGE}/scripts/${item}" "${tc}/scripts/${item}"
    done
    if [[ "$MODE" == "apply" ]]; then
        chmod +x "${tc}/scripts/autopilot.sh" 2>/dev/null || true
    fi
    log "    scripts: replaced ${SCRIPT_FILES[*]}"

    report_preserved "$tc"
    report_unclassified "$tc"
}

merge_kb_index_apply() {
    local tc="$1"
    NEW_INDEX="${tc}/kb/_index.yaml" \
    OLD_INDEX="${OLD_INDEX_FOR_MERGE}" \
    MERGED_OUT="${tc}/kb/_index.yaml" python3 - <<'PYEOF'
import os, sys, yaml

new_path = os.environ["NEW_INDEX"]
old_path = os.environ["OLD_INDEX"]
out_path = os.environ["MERGED_OUT"]

try:
    new_doc = yaml.safe_load(open(new_path))
    old_doc = yaml.safe_load(open(old_path)) if os.path.exists(old_path) else {}
    new_domains = new_doc.get("domains") or {}
    old_domains = (old_doc or {}).get("domains") or {}
    missing = {k: v for k, v in old_domains.items() if k not in new_domains}

    if not missing:
        print("    kb/_index.yaml: no target-only domains — payload index used as-is")
        sys.exit(0)

    block = yaml.safe_dump(missing, default_flow_style=False, sort_keys=True, allow_unicode=True)
    indented = "".join("  " + line + "\n" for line in block.splitlines())
    merged_text = (
        open(new_path).read().rstrip("\n")
        + "\n\n  # --- target-only domains (preserved by rollout-agentspec.sh) ---\n"
        + indented
    )

    parsed = yaml.safe_load(merged_text)
    merged_domains = parsed.get("domains") or {}
    if set(merged_domains) != set(new_domains) | set(missing):
        raise ValueError("merged domain set mismatch")

    with open(out_path, "w") as fh:
        fh.write(merged_text)
    print(f"    kb/_index.yaml: merged {len(missing)} target-only domains: {', '.join(sorted(missing))}")
except Exception as exc:
    print(f"    kb/_index.yaml merge error: {exc}", file=sys.stderr)
    sys.exit(3)
PYEOF
}

# --- rollback ---------------------------------------------------------------

rollback_target() {
    local target="$1"
    local name src
    name="$(basename "$target")"
    src="${BACKUP_ROOT}/${STAMP}/${name}/.claude"

    log ""
    info "Rollback: ${target} from ${src}"
    if [[ ! -d "$src" ]]; then
        warn "no backup for ${name} at stamp ${STAMP} — skipping"
        FAILURES=$((FAILURES + 1))
        return 0
    fi
    rm -rf "${target}/.claude"
    cp -R "$src" "${target}/.claude"
    log "    restored"
}

# --- main -------------------------------------------------------------------

main() {
    parse_args "$@"
    require_python

    if [[ "$ROLLBACK" -eq 1 ]]; then
        [[ "$STAMP_GIVEN" -eq 1 ]] || die "--rollback requires --stamp (see ls ${BACKUP_ROOT})"
        local t
        for t in "${TARGETS[@]}"; do rollback_target "$t"; done
        [[ "$FAILURES" -eq 0 ]] || exit 1
        exit 0
    fi

    stage_payload

    if [[ "$MODE" == "dry-run" ]]; then
        info "DRY-RUN — no files will be written. Re-run with --apply to execute."
    else
        info "APPLY — backups: ${BACKUP_ROOT}/${STAMP}/"
    fi

    local t
    for t in "${TARGETS[@]}"; do sync_target "$t"; done

    log ""
    if [[ "$FAILURES" -gt 0 ]]; then
        warn "${FAILURES} target(s) skipped or failed"
        exit 1
    fi
    if [[ "$MODE" == "dry-run" ]]; then
        info "Dry-run complete. Apply with: scripts/rollout-agentspec.sh --apply"
    else
        info "Rollout complete. Rollback with: scripts/rollout-agentspec.sh --rollback --stamp ${STAMP}"
    fi
}

main "$@"
