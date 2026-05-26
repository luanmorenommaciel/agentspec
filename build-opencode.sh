#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# AgentSpec OpenCode Layer Builder
# =============================================================================
# Generates .opencode/ (a build artifact) from .claude/ (source of truth).
# .opencode/ is gitignored — it's regenerated on demand, validated by tests.
#
# What it does:
#   1. Copies agents, injecting permission: + mode: into frontmatter
#   2. Copies commands, fixing ${CLAUDE_PLUGIN_ROOT} bash blocks
#   3. Copies skills, fixing /agentspec: command references
#   4. Creates the plugin stub and opencode.json config
#
# Usage:
#   ./build-opencode.sh           Build the OpenCode layer
#   ./build-opencode.sh --help    Show this help
#
# The .claude/ source tree is NEVER modified — all transformations happen
# during copy, mirroring the build-plugin.sh contract.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/.claude"
OUTPUT_DIR="${SCRIPT_DIR}/.opencode"
EXTRAS_DIR="${SCRIPT_DIR}/plugin-extras"
TRANSFORM_SCRIPT="${SCRIPT_DIR}/scripts/transform-opencode-frontmatter.py"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { printf "${BLUE}[INFO]${NC} %s\n" "$1"; }
ok()    { printf "${GREEN}[OK]${NC} %s\n" "$1"; }
warn()  { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
error() { printf "${RED}[ERROR]${NC} %s\n" "$1" >&2; }

cleanup() {
    find "${OUTPUT_DIR:-.}" -name "*.tmp" -type f -delete 2>/dev/null || true
}
trap cleanup EXIT

# ─── Help ────────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    cat <<'EOF'
AgentSpec OpenCode Layer Builder

Generates .opencode/ from .claude/ source of truth. .opencode/ is a build
artifact (gitignored) — changes should be made to .claude/ and rebuilt.

Usage:
  ./build-opencode.sh           Build the OpenCode layer
  ./build-opencode.sh --help    Show this help

Output: .opencode/ directory ready for opencode to discover.
EOF
    exit 0
fi

# ─── Preflight ───────────────────────────────────────────────────────────────

if [[ ! -d "${SOURCE_DIR}" ]]; then
    error ".claude/ directory not found at ${SOURCE_DIR}"
    exit 1
fi

if [[ ! -f "${TRANSFORM_SCRIPT}" ]]; then
    error "${TRANSFORM_SCRIPT} not found"
    exit 1
fi

info "Building OpenCode layer from .claude/ ..."

# ─── Step 0: Regenerate agent-router ─────────────────────────────────────────
# Ensures the agent-router SKILL.md + routing.json reflect the current agent
# set before we copy skills.

if [[ -f "${SCRIPT_DIR}/scripts/generate-agent-router.py" ]]; then
    info "Regenerating agent-router..."
    python3 "${SCRIPT_DIR}/scripts/generate-agent-router.py" >/dev/null 2>&1 || {
        warn "agent-router regeneration failed — continuing with existing artifacts"
    }
fi

# ─── Step 1: Clean previous build ────────────────────────────────────────────

info "Cleaning previous .opencode/ build..."
rm -rf "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}"
ok "Output directory cleaned"

# ─── Step 2: Transform and copy agents ────────────────────────────────────────

info "Copying agents with OpenCode frontmatter..."
mkdir -p "${OUTPUT_DIR}/agents"

AGENT_COUNT=0
while IFS= read -r -d '' src; do
    rel_path="${src#"${SOURCE_DIR}/agents/"}"
    dst="${OUTPUT_DIR}/agents/${rel_path}"

    # Skip non-.md files (README.md, _template.md)
    if [[ "${src}" != *.md ]]; then
        continue
    fi

    # Skip template — it has placeholder frontmatter
    if [[ "$(basename "${src}")" == "_template.md" ]]; then
        continue
    fi

    mkdir -p "$(dirname "${dst}")"
    python3 "${TRANSFORM_SCRIPT}" "${src}" "${dst}" || {
        error "Failed to transform: ${rel_path}"
        exit 1
    }
    AGENT_COUNT=$((AGENT_COUNT + 1))
done < <(find "${SOURCE_DIR}/agents" -type f -print0)

ok "${AGENT_COUNT} agents copied"

# ─── Step 3: Copy commands ────────────────────────────────────────────────────

info "Copying commands..."
cp -r "${SOURCE_DIR}/commands" "${OUTPUT_DIR}/commands"

COMMAND_COUNT=$(find "${OUTPUT_DIR}/commands" -name "*.md" -not -name "README.md" | wc -l | tr -d ' ')

# Fix ${CLAUDE_PLUGIN_ROOT} references in OpenCode command copies
# OpenCode doesn't inject this variable — use relative paths instead.
while IFS= read -r -d '' file; do
    tmp="${file}.tmp"
    sed \
        -e 's|\${CLAUDE_PLUGIN_ROOT:-\.}/scripts/judge\.py|./scripts/judge.py|g' \
        -e 's|\${CLAUDE_PLUGIN_ROOT}/scripts/|./scripts/|g' \
        -e 's|\${CLAUDE_PLUGIN_ROOT}|./.claude|g' \
        "$file" > "$tmp" && mv "$tmp" "$file" || { rm -f "$tmp"; exit 1; }
done < <(find "${OUTPUT_DIR}/commands" -type f \( -name "*.md" \) -print0)

ok "${COMMAND_COUNT} commands copied"

# ─── Step 4: Copy skills ──────────────────────────────────────────────────────

info "Copying skills..."
if [[ -d "${SOURCE_DIR}/skills" ]]; then
    cp -r "${SOURCE_DIR}/skills" "${OUTPUT_DIR}/skills"
fi

# Also copy plugin-extras skills (sdd-workflow, data-engineering-guide)
if [[ -d "${EXTRAS_DIR}/skills" ]]; then
    for skill_dir in "${EXTRAS_DIR}/skills/"*/; do
        [[ -d "${skill_dir}" ]] || continue
        skill_name="$(basename "${skill_dir}")"
        mkdir -p "${OUTPUT_DIR}/skills/${skill_name}"
        if [[ -f "${skill_dir}/SKILL.md" ]]; then
            cp "${skill_dir}/SKILL.md" "${OUTPUT_DIR}/skills/${skill_name}/SKILL.md"
        fi
        # Copy supporting files (templates, references, etc.)
        for item in "${skill_dir}"*; do
            if [[ "${item}" != *"/SKILL.md" ]] && [[ -f "${item}" ]]; then
                cp "${item}" "${OUTPUT_DIR}/skills/${skill_name}/"
            fi
        done
    done
fi

# Fix /agentspec: references → /commandname (no namespace in OpenCode)
while IFS= read -r -d '' file; do
    tmp="${file}.tmp"
    sed -e 's|/agentspec:|/|g' "$file" > "$tmp" && mv "$tmp" "$file" || { rm -f "$tmp"; exit 1; }
done < <(find "${OUTPUT_DIR}/skills" -type f -name "SKILL.md" -print0 2>/dev/null || true)

SKILL_COUNT=$(find "${OUTPUT_DIR}/skills" -name "SKILL.md" | wc -l | tr -d ' ')
ok "${SKILL_COUNT} skills copied"

# ─── Step 5: Create plugin stub ───────────────────────────────────────────────

info "Creating plugin stub..."
mkdir -p "${OUTPUT_DIR}/plugins"
cat > "${OUTPUT_DIR}/plugins/init-workspace.js" << 'PLUGINJS'
export const InitWorkspace = async ({ directory, $ }) => {
  return {
    "session.created": async () => {
      await $`mkdir -p .claude/sdd/features .claude/sdd/reports .claude/sdd/archive .opencode/storage`;
    }
  };
};
PLUGINJS
ok "Plugin stub created"

# ─── Step 6: Generate opencode.json ───────────────────────────────────────────

info "Generating opencode.json..."
cat > "${OUTPUT_DIR}/opencode.json" << 'OPCONF'
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "CLAUDE.md",
    "AGENTS.md"
  ],
  "permission": {
    "skill": { "*": "allow" },
    "edit": "allow",
    "bash": {
      "*": "ask",
      "git status": "allow",
      "git diff": "allow",
      "git log*": "allow",
      "python3 *": "allow",
      "ls*": "allow",
      "find*": "allow",
      "mkdir*": "allow",
      "cp*": "allow",
      "rm*": "ask"
    }
  }
}
OPCONF
ok "opencode.json generated"

# ─── Step 7: Summary ─────────────────────────────────────────────────────────

echo ""
echo "============================================"
printf "${GREEN}OpenCode Layer Build Complete${NC}\n"
echo "============================================"
echo "  Agents:   ${AGENT_COUNT}"
echo "  Commands: ${COMMAND_COUNT}"
echo "  Skills:   ${SKILL_COUNT}"
echo ""
echo "  Output:   ${OUTPUT_DIR}/"
echo ""
echo "  Test with:"
echo "    make test-opencode"
echo "============================================"
