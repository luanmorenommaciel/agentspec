#!/usr/bin/env bash
# =============================================================================
# share.sh — Share Visual Explainer HTML via Vercel
#
# Deploys a single HTML file to Vercel and returns the live URL. No auth
# required — uses Vercel's public deploy flow.
#
# Prerequisites:
#   - vercel CLI installed (npm install -g vercel)
#   - bash, mktemp, grep
#
# Usage:
#   ./share.sh <html-file>                # deploy and print URL
#   ./share.sh --help                     # show usage
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

show_help() {
  cat <<EOF
Usage: $(basename "$0") <html-file>

Deploys a single HTML file to Vercel and returns the live URL.

Options:
  --help, -h    Show this help message

Examples:
  $(basename "$0") diagram.html
EOF
  exit 0
}

# Parse --help before positional args
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
  show_help
fi

HTML_FILE="${1:-}"

if [[ -z "${HTML_FILE}" ]]; then
    printf "${RED}Error: Please provide an HTML file to share${NC}\n" >&2
    printf "Usage: %s <html-file>\n" "$(basename "$0")" >&2
    exit 1
fi

if [[ ! -f "${HTML_FILE}" ]]; then
    printf "${RED}Error: File not found: %s${NC}\n" "${HTML_FILE}" >&2
    exit 1
fi

# Find vercel-deploy skill
VERCEL_SCRIPT=""
for dir in ~/.pi/agent/skills/vercel-deploy/scripts /mnt/skills/user/vercel-deploy/scripts; do
    if [[ -f "${dir}/deploy.sh" ]]; then
        VERCEL_SCRIPT="${dir}/deploy.sh"
        break
    fi
done

if [[ -z "${VERCEL_SCRIPT}" ]]; then
    printf "${RED}Error: vercel-deploy skill not found${NC}\n" >&2
    printf "Install it with: pi install npm:vercel-deploy\n" >&2
    exit 1
fi

# Create temp directory with index.html
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TEMP_DIR}"' EXIT

# Copy file as index.html (Vercel serves index.html at root)
cp "${HTML_FILE}" "${TEMP_DIR}/index.html"

printf "${CYAN}Sharing %s...${NC}\n" "$(basename "${HTML_FILE}")" >&2

# Deploy via vercel-deploy skill — capture failures explicitly without set +e
RESULT=""
DEPLOY_EXIT=0
RESULT="$(bash "${VERCEL_SCRIPT}" "${TEMP_DIR}" 2>&1)" || DEPLOY_EXIT=$?

if [[ ${DEPLOY_EXIT} -ne 0 ]]; then
    printf "${RED}Error: Deployment failed${NC}\n" >&2
    printf "%s\n" "${RESULT}" >&2
    exit 1
fi

# Extract preview URL
PREVIEW_URL="$(grep -oE 'https://[^"]+\.vercel\.app' <<< "${RESULT}" | head -1)"
CLAIM_URL="$(grep -oE 'https://vercel\.com/claim-deployment[^"]+' <<< "${RESULT}" | head -1)"

if [[ -z "${PREVIEW_URL}" ]]; then
    printf "${RED}Error: Deployment failed${NC}\n" >&2
    printf "%s\n" "${RESULT}" >&2
    exit 1
fi

printf "\n" >&2
printf "${GREEN}✓ Shared successfully!${NC}\n\n" >&2
printf "${GREEN}Live URL:  %s${NC}\n" "${PREVIEW_URL}" >&2
printf "${CYAN}Claim URL: %s${NC}\n\n" "${CLAIM_URL}" >&2

# Output JSON for programmatic use (extract from vercel-deploy output)
grep -E '^\{' <<< "${RESULT}" | head -1
