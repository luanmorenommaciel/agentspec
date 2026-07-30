# scripts/ — Trust Layer do Pod D3

Materializacao em codigo do design apresentado pelo Carlos no deck
**"AgentSpec Assinado — Cosign para Integridade de Supply Chain"** (Sync Crew D · 2026-07-15).

## O que faz

Uma cadeia de confianca em 4 passos pra garantir a integridade dos arquivos
distribuidos pelo plugin AgentSpec (58 agentes, 31 comandos, 24 KB domains):

1. **Hash** — `generate_manifest.py` varre uma pasta e grava SHA-256 de cada arquivo
2. **Assinar** — `sign_manifest.sh` assina o manifest com cosign keyless (Sigstore/OIDC)
3. **Distribuir** — o manifest + bundle Sigstore viajam com o plugin
4. **Verificar** — `verify_signature.sh` valida assinatura e recomputa os hashes

## Requisitos

- Python 3.10+
- `cosign` (`brew install cosign`)
- Login OIDC valido (Google/GitHub) — abre browser na primeira vez

## Uso tipico

```bash
# 1. Publicar (quando shippar uma nova versao do plugin)
python3 scripts/generate_manifest.py --dir .claude/agents/data-engineering
bash scripts/sign_manifest.sh

# 2. Verificar (o Session Hook fara isso automaticamente no futuro)
bash scripts/verify_signature.sh
# → "OK: assinatura valida e todos os arquivos batem."
```

## Arquivos produzidos

- `security/manifest.json` — lista de arquivos + hashes + metadata git
- `security/manifest.sigstore.json` — bundle de assinatura Sigstore

## Cenarios de falha detectados pelo verify

- **MODIFICADO** — hash mudou (alguem editou o arquivo depois de assinar)
- **REMOVIDO** — arquivo listado no manifest sumiu do disco
- **NAO REGISTRADO** — arquivo novo no disco que nao esta no manifest (backdoor)

## Ponto aberto (conhecido, V0)

O `verify_signature.sh` usa `--certificate-identity-regexp=".*"` — aceita QUALQUER
assinatura, e nao apenas a de um signatario autorizado. **Isso e V0 do trust layer.**
V1 vai fixar na identidade OIDC especifica (ex.: `--certificate-identity="giulia.luca@owshq.com"`).

## Autoria

- **Design:** Carlos Medeiros (Pod D3) — deck de 15/jul/2026
- **Implementacao:** Giulia Parede (Pod D3) — 22/jul/2026, baseada em spec do deck
- **A revisar com:** Carlos, pra confirmar fidelidade do codigo ao design original
