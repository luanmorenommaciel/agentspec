#!/usr/bin/env bash
# =============================================================================
# autopilot.sh — AgentSpec Autopilot Headless Runner
#
# Headless (CI/cron) entrypoint for Autopilot. This script carries ZERO
# workflow policy: no gate logic, no retry logic, no phase knowledge. All of
# that lives in the sdd-autopilot skill and is exercised by Claude inside a
# single `claude -p '/auto ...'` invocation. This script only does: preflight
# checks, that one invocation, reads the terminal state from the RUN REPORT
# the skill writes, fires best-effort notifications, and maps the report's
# status to a process exit code.
#
# Prerequisites:
#   - claude CLI on PATH (https://claude.com/claude-code)
#   - run from inside a git repository (any subdirectory — the script cd's
#     to the repository root before invoking claude)
#   - the AgentSpec /auto command available: vendored at
#     .claude/commands/workflow/auto.md, or installed as a plugin
#
# Usage:
#   ./autopilot.sh "<intent>" [passthrough flags]
#   ./autopilot.sh --help
#
# Passthrough flags (forwarded verbatim to /auto — semantics owned by the
# sdd-autopilot skill, not this script):
#   --no-brainstorm --no-judge --no-ship --no-pr --max-iterations N
#
# Environment variables:
#   AUTOPILOT_TIMEOUT_MIN   Minutes before the claude invocation is killed
#                           (default: 60). Uses `timeout`/`gtimeout`; runs
#                           without a timeout (with a warning) if neither
#                           binary is available.
#   AUTOPILOT_WEBHOOK_URL   If set, POSTs a {status, report} JSON payload to
#                           this URL after the run (best-effort, 10s cap).
#                           The URL itself is never logged or printed.
#   AUTOPILOT_LOG           If set, the headless session transcript is also
#                           appended to this path.
#
# Exit codes:
#   0   RUN REPORT Status contains "Success" and is not partial
#   1   RUN REPORT Status contains "Aborted"
#   2   Preflight failure, or the RUN REPORT is missing / its status is
#       unreadable
#   3   RUN REPORT Status contains "Partial Success"
# =============================================================================

set -euo pipefail

readonly AUTO_COMMAND_RELATIVE_PATH=".claude/commands/workflow/auto.md"

INTENT=""
PASSTHROUGH_ARGS=()
REPO_ROOT=""
TIMEOUT_MIN="${AUTOPILOT_TIMEOUT_MIN:-60}"
TIMEOUT_BIN=""
PROMPT=""
INVOKE_EXIT=0
REPORT_PATH=""
RUN_MARKER=""
STATUS_LINE=""
STATUS_VALUE=""
FEATURE_VALUE=""
PR_URL=""
EXIT_CODE=2

print_usage() {
    cat <<EOF
Usage: $(basename "$0") "<intent>" [passthrough flags]
       $(basename "$0") --help

Runs the full AgentSpec SDD workflow autonomously from a single intent via
a headless 'claude -p "/auto ..."' invocation. All gate/retry/phase policy
lives in the sdd-autopilot skill — this script only preflights, invokes,
reads the RUN REPORT, and notifies.

Arguments:
  <intent>                  The feature intent, in quotes (required)

Passthrough flags (forwarded to /auto verbatim):
  --no-brainstorm           Skip Phase 0; intent feeds Define directly
  --no-judge                Skip the judge gate everywhere
  --no-ship                 Stop after Build; no archive
  --no-pr                   No PR; the branch is the deliverable
  --max-iterations N        Run-wide cap on lint/judge regenerations

Environment variables:
  AUTOPILOT_TIMEOUT_MIN      Minutes before the invocation is killed (default: 60)
  AUTOPILOT_WEBHOOK_URL      Best-effort webhook notified with {status, report}
  AUTOPILOT_LOG              Path to also append the session transcript to

Exit codes:
  0   RUN REPORT Status contains "Success" and is not partial
  1   RUN REPORT Status contains "Aborted"
  2   Preflight failure, or no readable RUN REPORT status
  3   RUN REPORT Status contains "Partial Success"

Examples:
  $(basename "$0") "Add a --dry-run flag to scripts/rollout-agentspec.sh"
  $(basename "$0") "Add retry to the ingest job" --no-brainstorm --no-ship
EOF
}

fail_preflight() {
    printf 'ERROR: %s\n' "$1" >&2
    exit 2
}

parse_args() {
    if [[ $# -gt 0 ]]; then
        case "$1" in
            --help | -h)
                print_usage
                exit 0
                ;;
        esac
    fi

    if [[ $# -eq 0 ]]; then
        print_usage >&2
        fail_preflight "missing required <intent> argument"
    fi

    INTENT="$1"
    shift
    PASSTHROUGH_ARGS=("$@")
}

auto_command_resolves() {
    [[ -f "${REPO_ROOT}/${AUTO_COMMAND_RELATIVE_PATH}" ]] && return 0

    if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]] && [[ -f "${CLAUDE_PLUGIN_ROOT}/commands/workflow/auto.md" ]]; then
        return 0
    fi

    compgen -G "${HOME}/.claude/plugins/*/commands/workflow/auto.md" >/dev/null 2>&1
}

run_preflight_checks() {
    command -v claude >/dev/null 2>&1 \
        || fail_preflight "claude CLI not found on PATH — install Claude Code: https://claude.com/claude-code"

    local repo_root
    repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" \
        || fail_preflight "not inside a git repository — cd into a git-tracked project and retry"
    cd "$repo_root" \
        || fail_preflight "failed to cd into repository root: ${repo_root}"
    REPO_ROOT="$repo_root"

    auto_command_resolves \
        || fail_preflight "AgentSpec /auto command not found — install the AgentSpec plugin or vendor .claude/ into this repository"
}

resolve_timeout_binary() {
    if command -v timeout >/dev/null 2>&1; then
        TIMEOUT_BIN="timeout"
    elif command -v gtimeout >/dev/null 2>&1; then
        TIMEOUT_BIN="gtimeout"
    else
        TIMEOUT_BIN=""
    fi
}

escape_for_double_quotes() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    printf '%s' "$value"
}

build_prompt() {
    local escaped_intent
    escaped_intent="$(escape_for_double_quotes "$INTENT")"
    PROMPT="/auto \"${escaped_intent}\""

    if [[ ${#PASSTHROUGH_ARGS[@]} -gt 0 ]]; then
        PROMPT+=" ${PASSTHROUGH_ARGS[*]}"
    fi
}

invoke_claude() {
    build_prompt
    RUN_MARKER="$(mktemp "${TMPDIR:-/tmp}/agentspec-autopilot.XXXXXX")" \
        || fail_preflight "could not create run marker"

    local log_target="${AUTOPILOT_LOG:-/dev/null}"
    if [[ -n "${AUTOPILOT_LOG:-}" ]]; then
        mkdir -p "$(dirname "$AUTOPILOT_LOG")" 2>/dev/null || true
    fi

    INVOKE_EXIT=0
    if [[ -n "$TIMEOUT_BIN" ]]; then
        "$TIMEOUT_BIN" "${TIMEOUT_MIN}m" claude -p "$PROMPT" --permission-mode acceptEdits 2>&1 \
            | tee -a "$log_target" || INVOKE_EXIT=$?
    else
        printf 'WARNING: no timeout binary found (install coreutils for gtimeout on macOS) — running without a timeout\n' >&2
        claude -p "$PROMPT" --permission-mode acceptEdits 2>&1 \
            | tee -a "$log_target" || INVOKE_EXIT=$?
    fi

    if [[ "$INVOKE_EXIT" -ne 0 ]]; then
        printf 'NOTE: claude invocation exited with code %s — deferring to the RUN REPORT status for the final exit code\n' "$INVOKE_EXIT" >&2
    fi
}

find_latest_report() {
    # Only consider a report created or updated by this invocation. Selecting
    # the latest report in the repository can turn a pre-OPEN failure into a
    # false success by reading a previous run.
    REPORT_PATH="$(
        find .claude/sdd/reports -maxdepth 1 -type f \
            -name 'AUTOPILOT_RUN_*.md' -newer "$RUN_MARKER" \
            -exec ls -t {} + 2>/dev/null | head -1
    )" || true
    rm -f "$RUN_MARKER"
    RUN_MARKER=""
}

extract_status() {
    if [[ -z "${REPORT_PATH:-}" ]]; then
        printf 'WARNING: no AUTOPILOT_RUN report found under .claude/sdd/reports/ — the run never reached its OPEN step\n' >&2
    fi

    STATUS_LINE="$(grep -m1 '^| \*\*Status\*\*' "${REPORT_PATH:-/dev/null}" 2>/dev/null)" || STATUS_LINE="unknown"

    if [[ "$STATUS_LINE" == "unknown" ]] && [[ -n "${REPORT_PATH:-}" ]]; then
        printf 'WARNING: report found but its Status row is unreadable: %s\n' "$REPORT_PATH" >&2
    fi

    STATUS_VALUE="$(printf '%s\n' "$STATUS_LINE" | sed -E 's/^\| \*\*Status\*\* \| (.*) \|$/\1/')"
    if [[ "$STATUS_VALUE" == "$STATUS_LINE" ]] || [[ -z "$STATUS_VALUE" ]]; then
        STATUS_VALUE="$STATUS_LINE"
    fi

    FEATURE_VALUE="$(grep -m1 '^| \*\*Feature\*\*' "${REPORT_PATH:-/dev/null}" 2>/dev/null \
        | sed -E 's/^\| \*\*Feature\*\* \| (.*) \|$/\1/')" || FEATURE_VALUE=""
    PR_URL="$(printf '%s\n' "$STATUS_VALUE" \
        | sed -nE 's/^.*PR: (https?:[^)]+).*$/\1/p')"
}

notify_terminal() {
    printf 'Autopilot run complete\n' || true
    printf '  Status : %s\n' "$STATUS_VALUE" || true
    printf '  Report : %s\n' "${REPORT_PATH:-none}" || true
}

notify_os() {
    case "$(uname -s)" in
        Darwin)
            osascript -e "display notification \"$(escape_for_double_quotes "$STATUS_VALUE")\" with title \"Autopilot\"" >/dev/null 2>&1 || true
            ;;
        Linux)
            command -v notify-send >/dev/null 2>&1 && notify-send "Autopilot" "$STATUS_VALUE" || true
            ;;
    esac
}

notify_webhook() {
    [[ -z "${AUTOPILOT_WEBHOOK_URL:-}" ]] && return 0

    local payload
    payload="$(printf '{"feature":"%s","status":"%s","pr_url":"%s","report_path":"%s"}' \
        "$(escape_for_double_quotes "$FEATURE_VALUE")" \
        "$(escape_for_double_quotes "$STATUS_VALUE")" \
        "$(escape_for_double_quotes "$PR_URL")" \
        "$(escape_for_double_quotes "${REPORT_PATH:-}")")"

    curl -m 10 -fsS -X POST "$AUTOPILOT_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "$payload" >/dev/null 2>&1 || true
}

notify() {
    notify_terminal
    notify_os
    notify_webhook
}

compute_exit_code() {
    case "$STATUS_VALUE" in
        *Partial\ Success*) EXIT_CODE=3 ;;
        *Success*) EXIT_CODE=0 ;;
        *Aborted*) EXIT_CODE=1 ;;
        *) EXIT_CODE=2 ;;
    esac
}

main() {
    parse_args "$@"
    run_preflight_checks
    resolve_timeout_binary
    invoke_claude
    find_latest_report
    extract_status
    compute_exit_code
    notify
    exit "$EXIT_CODE"
}

main "$@"
