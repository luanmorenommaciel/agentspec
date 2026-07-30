#!/usr/bin/env bash
# sign_manifest.sh — Assina o manifest.json usando cosign (Sigstore keyless).
#
# Materializa em codigo o passo 2 (ASSINAR) do deck do Carlos.
# Nao gerencia chaves: usa OIDC (Google, GitHub) na hora do sign, e o registro
# publico do Rekor guarda a prova de que voce assinou.
#
# Uso:
#     bash scripts/sign_manifest.sh                        # assina security/manifest.json
#     bash scripts/sign_manifest.sh caminho/manifest.json
#
# Requer:
#     - cosign (brew install cosign)
#     - Login OIDC valido (Google ou GitHub) — abre navegador na primeira vez

# -e: para no primeiro erro; -u: erro se variavel nao definida; -o pipefail: erro em pipe
set -euo pipefail

# Caminho do manifest (default: security/manifest.json)
MANIFEST_PATH="${1:-security/manifest.json}"
# Onde salvar a assinatura (bundle Sigstore no mesmo diretorio, com sufixo .sigstore.json)
BUNDLE_PATH="${MANIFEST_PATH%.json}.sigstore.json"

# Confere que o manifest existe antes de tentar assinar
if [[ ! -f "$MANIFEST_PATH" ]]; then
    echo "ERRO: manifest nao encontrado em $MANIFEST_PATH" >&2
    echo "     Rode antes: python3 scripts/generate_manifest.py --dir <pasta>" >&2
    exit 1
fi

# Confere que o cosign esta instalado
if ! command -v cosign &> /dev/null; then
    echo "ERRO: cosign nao esta instalado." >&2
    echo "     Instale com: brew install cosign" >&2
    exit 1
fi

echo "==> Assinando $MANIFEST_PATH..."
echo "    Bundle sera salvo em: $BUNDLE_PATH"
echo ""

# --new-bundle-format: formato de bundle moderno do cosign (2024+).
# --yes: nao pergunta confirmacao interativa (importante pra CI).
# O login OIDC acontece no browser na primeira vez; depois usa cache local.
cosign sign-blob "$MANIFEST_PATH" \
    --bundle "$BUNDLE_PATH" \
    --new-bundle-format \
    --yes

echo ""
echo "OK: assinatura gerada em $BUNDLE_PATH"
echo "    Registrada no Rekor (log publico de transparencia)."
