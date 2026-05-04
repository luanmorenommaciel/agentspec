#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# AgentSpec Plugin Builder
# =============================================================================
# Packages .claude/ (source of truth) into plugin/ (distributable plugin).
# Rewrites internal paths from .claude/ to ${CLAUDE_PLUGIN_ROOT}/ while
# preserving workspace paths (.claude/sdd/features, reports, archive, storage).
#
# Usage:
#   ./build-plugin.sh           # Build the plugin
#   ./build-plugin.sh --help    # Show this help
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/.claude"
PLUGIN_DIR="${SCRIPT_DIR}/plugin"
EXTRAS_DIR="${SCRIPT_DIR}/plugin-extras"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { printf "${BLUE}[INFO]${NC} %s\n" "$1"; }
ok()    { printf "${GREEN}[OK]${NC} %s\n" "$1"; }
warn()  { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
error() { printf "${RED}[ERROR]${NC} %s\n" "$1" >&2; }

# Cleanup trap for interrupted builds
cleanup() {
    find "${PLUGIN_DIR:-.}" -name "*.tmp" -type f -delete 2>/dev/null || true
}
trap cleanup EXIT

# ─── Help ────────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    cat <<'EOF'
AgentSpec Plugin Builder

Packages .claude/ (source of truth) into plugin/ (distributable plugin).
Rewrites internal paths to ${CLAUDE_PLUGIN_ROOT}/ and merges plugin-extras/.

Usage:
  ./build-plugin.sh           Build the plugin
  ./build-plugin.sh --help    Show this help

Output: plugin/ directory ready for `claude --plugin-dir ./plugin`
EOF
    exit 0
fi

# ─── Preflight ───────────────────────────────────────────────────────────────

if [[ ! -d "${SOURCE_DIR}" ]]; then
    error ".claude/ directory not found at ${SOURCE_DIR}"
    exit 1
fi

if [[ ! -f "${PLUGIN_DIR}/.claude-plugin/plugin.json" ]]; then
    error "plugin/.claude-plugin/plugin.json not found. Create the manifest first."
    exit 1
fi

info "Building AgentSpec plugin from .claude/ ..."

# ─── Step 0: Run Python tests ────────────────────────────────────────────────
# Fail fast if scripts/judge.py or scripts/generate-agent-router.py regress.
# Tests are skipped (with a warning, not an error) when pytest is not
# installed — we never block builds on a missing optional dev dependency.

if [[ -d "${SCRIPT_DIR}/tests" ]]; then
    if python3 -c "import pytest" 2>/dev/null; then
        info "Running Python tests..."
        if (cd "${SCRIPT_DIR}" && python3 -m pytest tests/ -q >/dev/null 2>&1); then
            ok "Python tests passed"
        else
            error "Python tests failed — run: python3 -m pytest tests/ -v"
            exit 1
        fi
    else
        warn "pytest not installed — skipping tests (pip install pytest to enable)"
    fi
fi

# ─── Step 0b: Regenerate agent-router from agent frontmatter ─────────────────
# Ensures .claude/skills/agent-router/SKILL.md and routing.json reflect the
# current agent set before we copy them into the plugin.

if [[ -f "${SCRIPT_DIR}/scripts/generate-agent-router.py" ]]; then
    info "Regenerating agent-router from agent frontmatter..."
    if python3 "${SCRIPT_DIR}/scripts/generate-agent-router.py" >/dev/null; then
        ok "agent-router regenerated"
    else
        error "agent-router generation failed"
        exit 1
    fi
else
    warn "scripts/generate-agent-router.py not found — skipping regeneration"
fi

# ─── Step 1: Clean previous build (preserve .claude-plugin/) ─────────────────

info "Cleaning previous build..."
find "${PLUGIN_DIR:?}" -mindepth 1 -maxdepth 1 \
    ! -name '.claude-plugin' \
    ! -name 'README.md' \
    -exec rm -rf {} +

ok "Previous build cleaned"

# ─── Step 2: Copy components ─────────────────────────────────────────────────

info "Copying agents..."
cp -r "${SOURCE_DIR}/agents" "${PLUGIN_DIR}/agents"

info "Copying commands..."
cp -r "${SOURCE_DIR}/commands" "${PLUGIN_DIR}/commands"

if [[ -d "${SOURCE_DIR}/skills" ]]; then
    info "Copying skills..."
    cp -r "${SOURCE_DIR}/skills" "${PLUGIN_DIR}/skills"
else
    warn ".claude/skills/ not found — creating empty skills dir"
    mkdir -p "${PLUGIN_DIR}/skills"
fi

info "Copying KB domains..."
cp -r "${SOURCE_DIR}/kb" "${PLUGIN_DIR}/kb"

info "Copying SDD templates and architecture..."
mkdir -p "${PLUGIN_DIR}/sdd"
cp -r "${SOURCE_DIR}/sdd/templates" "${PLUGIN_DIR}/sdd/templates"
cp -r "${SOURCE_DIR}/sdd/architecture" "${PLUGIN_DIR}/sdd/architecture"

# Copy SDD index and README if they exist
[[ -f "${SOURCE_DIR}/sdd/_index.md" ]] && cp "${SOURCE_DIR}/sdd/_index.md" "${PLUGIN_DIR}/sdd/"
[[ -f "${SOURCE_DIR}/sdd/README.md" ]] && cp "${SOURCE_DIR}/sdd/README.md" "${PLUGIN_DIR}/sdd/"

ok "All components copied"

# ─── Step 2b: Copy plugin-extras (plugin-only content) ───────────────────────

if [[ -d "${EXTRAS_DIR}" ]]; then
    info "Copying plugin-extras (new skills, hooks, scripts)..."
    if [[ -d "${EXTRAS_DIR}/skills" ]] && ls "${EXTRAS_DIR}/skills/"* >/dev/null 2>&1; then
        cp -r "${EXTRAS_DIR}/skills/"* "${PLUGIN_DIR}/skills/"
    fi
    [[ -d "${EXTRAS_DIR}/hooks" ]] && cp -r "${EXTRAS_DIR}/hooks" "${PLUGIN_DIR}/"
    [[ -d "${EXTRAS_DIR}/scripts" ]] && cp -r "${EXTRAS_DIR}/scripts" "${PLUGIN_DIR}/"
    ok "Plugin-extras copied"
fi

# ─── Step 3: Remove workspace-specific directories ───────────────────────────

info "Removing workspace-specific directories from plugin..."
rm -rf "${PLUGIN_DIR:?}/sdd/features"
rm -rf "${PLUGIN_DIR:?}/sdd/reports"
rm -rf "${PLUGIN_DIR:?}/sdd/archive"

# Drop scaffolding files that exist for contributor use only and would
# confuse Claude Code's agent loader (placeholder frontmatter values).
find "${PLUGIN_DIR:?}/agents" -name '_template.md' -delete 2>/dev/null || true

ok "Workspace directories excluded"

# ─── Step 4: Path rewriting ──────────────────────────────────────────────────
#
# REWRITE (plugin-internal references):
#   .claude/kb/           → ${CLAUDE_PLUGIN_ROOT}/kb/
#   .claude/agents/       → ${CLAUDE_PLUGIN_ROOT}/agents/
#   .claude/commands/     → ${CLAUDE_PLUGIN_ROOT}/commands/
#   .claude/skills/       → ${CLAUDE_PLUGIN_ROOT}/skills/
#   .claude/sdd/templates/     → ${CLAUDE_PLUGIN_ROOT}/sdd/templates/
#   .claude/sdd/architecture/  → ${CLAUDE_PLUGIN_ROOT}/sdd/architecture/
#   .claude/sdd/_index.md      → ${CLAUDE_PLUGIN_ROOT}/sdd/_index.md
#   .claude/sdd/README.md      → ${CLAUDE_PLUGIN_ROOT}/sdd/README.md
#
# PRESERVE (workspace output paths — must NOT be rewritten):
#   .claude/sdd/features/  → stays as-is (user's project)
#   .claude/sdd/reports/   → stays as-is (user's project)
#   .claude/sdd/archive/   → stays as-is (user's project)
#   .claude/storage/       → stays as-is (user's project)
# ─────────────────────────────────────────────────────────────────────────────

info "Rewriting paths in .md, .yaml, and .json files..."

while IFS= read -r -d '' file; do
    tmp="${file}.tmp"
    sed \
        -e 's|\.claude/kb/|${CLAUDE_PLUGIN_ROOT}/kb/|g' \
        -e 's|\.claude/agents/|${CLAUDE_PLUGIN_ROOT}/agents/|g' \
        -e 's|\.claude/commands/|${CLAUDE_PLUGIN_ROOT}/commands/|g' \
        -e 's|\.claude/skills/|${CLAUDE_PLUGIN_ROOT}/skills/|g' \
        -e 's|\.claude/sdd/templates/|${CLAUDE_PLUGIN_ROOT}/sdd/templates/|g' \
        -e 's|\.claude/sdd/architecture/|${CLAUDE_PLUGIN_ROOT}/sdd/architecture/|g' \
        -e 's|\.claude/sdd/_index\.md|${CLAUDE_PLUGIN_ROOT}/sdd/_index.md|g' \
        -e 's|\.claude/sdd/README\.md|${CLAUDE_PLUGIN_ROOT}/sdd/README.md|g' \
        "$file" > "$tmp" && mv "$tmp" "$file" || { rm -f "$tmp"; exit 1; }
done < <(find "${PLUGIN_DIR}" \( -name "*.md" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
    -type f ! -path "${PLUGIN_DIR}/.claude-plugin/*" -print0)

ok "Paths rewritten"

# ─── Step 5: Rewrite hardcoded absolute paths ────────────────────────────────
# After Step 4, some paths may look like:
#   /Users/username/GitHub/agentspec/${CLAUDE_PLUGIN_ROOT}/skills/...
# We need to strip the absolute prefix, leaving just ${CLAUDE_PLUGIN_ROOT}/...
# Also catch any remaining /Users/.../agentspec/.claude/ patterns.

info "Rewriting absolute paths..."
while IFS= read -r -d '' file; do
    tmp="${file}.tmp"
    sed \
        -e 's|/[^ ]*\${CLAUDE_PLUGIN_ROOT}/|${CLAUDE_PLUGIN_ROOT}/|g' \
        -e 's|/[^ ]*/\.claude/skills/|${CLAUDE_PLUGIN_ROOT}/skills/|g' \
        -e 's|cd \.claude/skills/|cd ${CLAUDE_PLUGIN_ROOT}/skills/|g' \
        "$file" > "$tmp" && mv "$tmp" "$file" || { rm -f "$tmp"; exit 1; }
done < <(find "${PLUGIN_DIR}" -type f \( -name "*.md" -o -name "*.py" -o -name "*.sh" \) \
    ! -path "${PLUGIN_DIR}/.claude-plugin/*" -print0)

ok "Absolute paths rewritten"

# ─── Step 5b: Restore executable permissions (lost during sed tmp→mv) ────────

chmod +x "${PLUGIN_DIR}/scripts/"*.sh 2>/dev/null || true

# ─── Step 6: Verify no stale .claude/ paths remain ──────────────────────────

info "Verifying path migration..."

# Collect stale references (grep returns 1 on no match — use || true)
_stale_filter() {
    grep -r '\.claude/' "${PLUGIN_DIR}" \
        --include="*.md" --include="*.yaml" --include="*.yml" \
        | grep -v 'CLAUDE_PLUGIN_ROOT' \
        | grep -v '\.claude/sdd/features' \
        | grep -v '\.claude/sdd/reports' \
        | grep -v '\.claude/sdd/archive' \
        | grep -v '\.claude/sdd/' \
        | grep -v '\.claude/storage' \
        | grep -v '\.claude-plugin' \
        | grep -v '\.claude/settings' \
        | grep -v 'CLAUDE\.md' \
        | grep -v '\.claude/plans' \
        | grep -v '\.claude/memory' \
        | grep -v '^[[:space:]]*#' \
        || true
}

STALE_OUTPUT=$(_stale_filter)
STALE_COUNT=$(printf '%s' "${STALE_OUTPUT}" | grep -c '.' || true)

if [[ "${STALE_COUNT}" -gt 0 ]]; then
    warn "${STALE_COUNT} potentially stale .claude/ references found:"
    printf '%s\n' "${STALE_OUTPUT}" | head -20
    echo ""
    warn "Review the above references — some may be intentional (workspace paths)."
else
    ok "No stale .claude/ paths found"
fi

# ─── Step 7: Summary ─────────────────────────────────────────────────────────

AGENT_COUNT=$(find "${PLUGIN_DIR}/agents" -name "*.md" -not -name "README.md" -not -name "_template.md" | wc -l | tr -d ' ')
COMMAND_COUNT=$(find "${PLUGIN_DIR}/commands" -name "*.md" -not -name "README.md" | wc -l | tr -d ' ')
SKILL_COUNT=$(find "${PLUGIN_DIR}/skills" -name "SKILL.md" | wc -l | tr -d ' ')
KB_COUNT=$(find "${PLUGIN_DIR}/kb" -maxdepth 1 -type d ! -name "kb" ! -name "_templates" ! -name "shared" | wc -l | tr -d ' ')

echo ""
echo "============================================"
printf "${GREEN}AgentSpec Plugin Build Complete${NC}\n"
echo "============================================"
echo "  Agents:   ${AGENT_COUNT}"
echo "  Commands: ${COMMAND_COUNT}"
echo "  Skills:   ${SKILL_COUNT}"
echo "  KB:       ${KB_COUNT} domains"
echo ""
echo "  Output:   ${PLUGIN_DIR}/"
echo ""
echo "  Test with:"
echo "    claude --plugin-dir ./plugin"
echo ""
echo "  Validate with:"
echo "    claude plugin validate ./plugin"
echo "============================================"
