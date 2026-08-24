#!/usr/bin/env bash
# verify_signature.sh — Verifica assinatura + integridade do manifest.
#
# Materializa o passo 4 (VERIFICAR) COMPLETO do trust layer:
#   1. cosign verify-blob confirma que a assinatura e valida (a autoria)
#   2. verify_manifest.py confirma que cada arquivo bate com o hash listado (integridade)
#
# Uso:
#     bash scripts/verify_signature.sh                   # usa plugin-extras/security/manifest.json (canonical)
#     bash scripts/verify_signature.sh plugin/security/manifest.json  # verifica o built plugin
#
# Sai com:
#     exit 0 -> tudo OK (assinatura valida + hashes batem)
#     exit 1 -> qualquer falha
#
# NOTA IMPORTANTE (ponto aberto ja identificado):
# O --certificate-identity-regexp=".*" abaixo aceita QUALQUER assinatura.
# Isso e V0. Em producao/V1 precisamos fixar na identidade OIDC especifica
# (ex.: --certificate-identity="giulia.luca@owshq.com").

set -euo pipefail

MANIFEST_PATH="${1:-plugin-extras/security/manifest.json}"
BUNDLE_PATH="${MANIFEST_PATH%.json}.sigstore.json"

if [[ ! -f "$MANIFEST_PATH" ]]; then
    echo "ERROR: manifest not found at $MANIFEST_PATH" >&2
    exit 1
fi

if [[ ! -f "$BUNDLE_PATH" ]]; then
    echo "ERROR: signature bundle not found at $BUNDLE_PATH" >&2
    echo "       Run first: bash scripts/sign_manifest.sh" >&2
    exit 1
fi

if ! command -v cosign &> /dev/null; then
    echo "ERROR: cosign is not installed." >&2
    exit 1
fi

echo "==> [1/2] Verifying signature with cosign..."
cosign verify-blob "$MANIFEST_PATH" \
    --bundle "$BUNDLE_PATH" \
    --new-bundle-format \
    --certificate-identity-regexp=".*" \
    --certificate-oidc-issuer-regexp=".*"

echo ""
echo "==> [2/2] Verifying file integrity with verify_manifest.py..."

# Descobre onde este script mora pra achar verify_manifest.py no mesmo diretorio.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/verify_manifest.py" "$MANIFEST_PATH"

echo ""
echo "OK: signature valid and all files match."
