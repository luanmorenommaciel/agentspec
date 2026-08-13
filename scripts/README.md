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

O alvo padrao e o **`plugin/`** — o payload buildado que o consumidor recebe
via marketplace. Assinar `.claude/` (source) e possivel via `--dir`, mas nao
casa com o que o cliente instala (paths sao reescritos pelo `build-plugin.sh`).

```bash
# 1. Publicar (rodar apos `./build-plugin.sh` gerar plugin/)
python3 scripts/generate_manifest.py --dir plugin/agents/data-engineering
bash scripts/sign_manifest.sh

# 2. Verificar (o Session Hook fara isso automaticamente no futuro)
bash scripts/verify_signature.sh
# → "OK: assinatura valida e todos os arquivos batem."
```

## Arquivos produzidos

- `plugin/security/manifest.json` — lista de arquivos + hashes + metadata git
- `plugin/security/manifest.sigstore.json` — bundle de assinatura Sigstore

Ambos vivem sob `plugin/` **de proposito**: assim viajam junto quando o
consumidor instala o plugin via marketplace. Sao commitados no repo (nao
gitignorados) — o consumidor precisa deles pra rodar o verify.

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
