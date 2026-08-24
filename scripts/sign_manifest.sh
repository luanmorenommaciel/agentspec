#!/usr/bin/env bash
# sign_manifest.sh — Assina o manifest.json usando cosign (Sigstore keyless).
#
# Materializa em codigo o passo 2 (ASSINAR) do trust layer.
# Nao gerencia chaves: usa OIDC (Google, GitHub) na hora do sign, e o registro
# publico do Rekor guarda a prova de que voce assinou.
#
# Uso:
#     bash scripts/sign_manifest.sh                        # assina plugin-extras/security/manifest.json
#     bash scripts/sign_manifest.sh caminho/manifest.json
#
# Requer:
#     - cosign (brew install cosign)
#     - Login OIDC valido (Google ou GitHub) — abre navegador na primeira vez

# -e: para no primeiro erro; -u: erro se variavel nao definida; -o pipefail: erro em pipe
set -euo pipefail

# Caminho do manifest (default: plugin-extras/security/manifest.json — canonical source)
MANIFEST_PATH="${1:-plugin-extras/security/manifest.json}"
# Onde salvar a assinatura (bundle Sigstore no mesmo diretorio, com sufixo .sigstore.json)
BUNDLE_PATH="${MANIFEST_PATH%.json}.sigstore.json"

# Confere que o manifest existe antes de tentar assinar
if [[ ! -f "$MANIFEST_PATH" ]]; then
    echo "ERROR: manifest not found at $MANIFEST_PATH" >&2
    echo "       Run first: python3 scripts/generate_manifest.py --dir <folder>" >&2
    exit 1
fi

# Confere que o cosign esta instalado
if ! command -v cosign &> /dev/null; then
    echo "ERROR: cosign is not installed." >&2
    echo "       Install with: brew install cosign" >&2
    exit 1
fi

echo "==> Signing $MANIFEST_PATH..."
echo "    Bundle will be written to: $BUNDLE_PATH"
echo ""

# --new-bundle-format: formato de bundle moderno do cosign (2024+).
# --yes: nao pergunta confirmacao interativa (importante pra CI).
# O login OIDC acontece no browser na primeira vez; depois usa cache local.
cosign sign-blob "$MANIFEST_PATH" \
    --bundle "$BUNDLE_PATH" \
    --new-bundle-format \
    --yes

echo ""
echo "OK: signature written to $BUNDLE_PATH"
echo "    Recorded in Rekor (public transparency log)."
