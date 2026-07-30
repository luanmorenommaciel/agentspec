#!/usr/bin/env bash
# verify_signature.sh — Verifica assinatura + integridade do manifest.
#
# Materializa o passo 4 (VERIFICAR) COMPLETO do deck do Carlos:
#   1. cosign verify-blob confirma que a assinatura e valida (a autoria)
#   2. verify_manifest.py confirma que cada arquivo bate com o hash listado (integridade)
#
# Uso:
#     bash scripts/verify_signature.sh                   # usa security/manifest.json
#     bash scripts/verify_signature.sh caminho/manifest.json
#
# Sai com:
#     exit 0 -> tudo OK (assinatura valida + hashes batem)
#     exit 1 -> qualquer falha
#
# NOTA IMPORTANTE (ponto aberto identificado no deck):
# O --certificate-identity-regexp=".*" abaixo aceita QUALQUER assinatura.
# Isso e V0. Em producao/V1 precisamos fixar na identidade OIDC especifica
# (ex.: --certificate-identity="giulia.luca@owshq.com").

set -euo pipefail

MANIFEST_PATH="${1:-security/manifest.json}"
BUNDLE_PATH="${MANIFEST_PATH%.json}.sigstore.json"

if [[ ! -f "$MANIFEST_PATH" ]]; then
    echo "ERRO: manifest nao encontrado em $MANIFEST_PATH" >&2
    exit 1
fi

if [[ ! -f "$BUNDLE_PATH" ]]; then
    echo "ERRO: bundle de assinatura nao encontrado em $BUNDLE_PATH" >&2
    echo "     Rode antes: bash scripts/sign_manifest.sh" >&2
    exit 1
fi

if ! command -v cosign &> /dev/null; then
    echo "ERRO: cosign nao esta instalado." >&2
    exit 1
fi

echo "==> [1/2] Verificando assinatura com cosign..."
cosign verify-blob "$MANIFEST_PATH" \
    --bundle "$BUNDLE_PATH" \
    --new-bundle-format \
    --certificate-identity-regexp=".*" \
    --certificate-oidc-issuer-regexp=".*"

echo ""
echo "==> [2/2] Verificando integridade dos arquivos com verify_manifest.py..."

# Descobre onde este script mora pra achar verify_manifest.py no mesmo diretorio.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/verify_manifest.py" "$MANIFEST_PATH"

echo ""
echo "OK: assinatura valida e todos os arquivos batem."
