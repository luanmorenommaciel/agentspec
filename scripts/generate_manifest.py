#!/usr/bin/env python3
"""
generate_manifest.py — Gera um manifest JSON com hash SHA-256 dos arquivos.

Materializa em codigo o design apresentado pelo Carlos no deck
"AgentSpec Assinado — Cosign para Integridade de Supply Chain" (15/jul/2026).

Uso:
    python3 scripts/generate_manifest.py --dir .claude/agents/data-engineering
    python3 scripts/generate_manifest.py --dir .claude/agents --out security/manifest.json

O manifest resultante lista cada arquivo com seu SHA-256 + tamanho + metadata git.
Serve como entrada pro cosign sign-blob (que assina o manifest todo com uma unica signature).
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Extensoes aceitas por padrao (conforme deck do Carlos).
# Sao os tipos de arquivo que compoem o plugin AgentSpec.
DEFAULT_EXTENSIONS = [".md", ".yaml", ".yml", ".json", ".toml"]

# Versao do schema do manifest. Se o formato mudar no futuro, subimos essa versao
# pra deteccao de compatibilidade nos scripts de verify.
SCHEMA_VERSION = "1.0"


def sha256_of_file(path: Path) -> str:
    """Computa o SHA-256 de um arquivo, lendo em pedacos pra nao estourar memoria."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        # Le em pedacos de 64KB — funciona pra arquivo pequeno (.md) ou grande (.json).
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_metadata(repo_root: Path) -> dict:
    """Extrai metadados do git (commit, branch, dirty) pra proveniencia.

    Se qualquer comando git falhar (ex.: repo baixado sem historico), retornamos
    None nos campos correspondentes — o manifest ainda funciona sem git.
    """

    def run(cmd):
        try:
            return subprocess.check_output(
                cmd, cwd=repo_root, stderr=subprocess.DEVNULL
            ).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    commit = run(["git", "rev-parse", "HEAD"])
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    # `git status --porcelain` retorna vazio se nao ha mudancas pendentes.
    status = run(["git", "status", "--porcelain"])
    is_dirty = bool(status) if status is not None else None

    return {
        "git_commit": commit,
        "git_branch": branch,
        "git_is_dirty": is_dirty,
    }


def scan_directory(target_dir: Path, allowed_extensions):
    """Percorre `target_dir` recursivamente e coleta arquivos com extensoes permitidas.

    Cada arquivo vira uma entrada com:
      - path (relativa a target_dir, com barras normalizadas)
      - sha256 (hex string)
      - size_bytes (int)
    """
    entries = []
    for file_path in sorted(target_dir.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in allowed_extensions:
            continue

        relative = file_path.relative_to(target_dir).as_posix()
        entries.append({
            "path": relative,
            "sha256": sha256_of_file(file_path),
            "size_bytes": file_path.stat().st_size,
        })

    return entries


def build_manifest(target_dir: Path, allowed_extensions, repo_root: Path) -> dict:
    """Monta o dicionario final do manifest, no formato acordado com o Carlos."""
    files = scan_directory(target_dir, allowed_extensions)

    # base_path relativa ao repo root, pro manifest ser portavel entre maquinas.
    try:
        base_path_str = target_dir.relative_to(repo_root).as_posix()
    except ValueError:
        base_path_str = str(target_dir)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "generate_manifest.py v1.0",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "algorithm": "sha256",
        "base_path": base_path_str,
        "allowed_extensions": sorted(allowed_extensions),
        "file_count": len(files),
        "git": git_metadata(repo_root),
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera manifest JSON com SHA-256 de arquivos (Pod D3 · Trust Layer)."
    )
    parser.add_argument(
        "--dir",
        required=True,
        type=Path,
        help="Pasta a escanear (ex.: .claude/agents/data-engineering)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("security/manifest.json"),
        help="Onde salvar o manifest (default: security/manifest.json)",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=DEFAULT_EXTENSIONS,
        help="Extensoes permitidas (default: .md .yaml .yml .json .toml)",
    )

    args = parser.parse_args()

    if not args.dir.is_dir():
        print(f"ERRO: {args.dir} nao e uma pasta valida.", file=sys.stderr)
        return 1

    # Descobre o repo root pra normalizar caminhos e ler metadata git.
    repo_root = Path.cwd()

    # Normaliza extensoes pra ter ponto e ser minusculas.
    exts = [e if e.startswith(".") else f".{e}" for e in args.extensions]
    exts = [e.lower() for e in exts]

    manifest = build_manifest(args.dir.resolve(), exts, repo_root)

    # Garante que a pasta de saida existe.
    args.out.parent.mkdir(parents=True, exist_ok=True)

    # sort_keys=True torna o JSON determinista (mesma entrada → mesmos bytes).
    with args.out.open("w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")  # newline final e boa pratica POSIX + Git

    print(f"OK: manifest com {manifest['file_count']} arquivos gerado em {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
