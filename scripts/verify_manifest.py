#!/usr/bin/env python3
"""
verify_manifest.py — Verifica que os arquivos batem com o manifest.

Materializa o passo 4 (VERIFICAR) do deck do Carlos, na parte de checagem de
integridade. NAO verifica a assinatura — isso e trabalho do verify_signature.sh
(que primeiro chama cosign verify-blob, e depois este script pra checar hashes).

Detecta tres tipos de divergencia:
    1. MODIFICADO — arquivo existe mas hash mudou
    2. REMOVIDO — arquivo listado no manifest sumiu do disco
    3. NAO REGISTRADO — arquivo no disco nao esta no manifest (backdoor injetado)

Uso:
    python3 scripts/verify_manifest.py                       # usa security/manifest.json
    python3 scripts/verify_manifest.py caminho/manifest.json

Sai com:
    exit 0 -> OK: todos batem
    exit 1 -> falha (qualquer divergencia encontrada)
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_of_file(path: Path) -> str:
    """Computa o SHA-256 de um arquivo (mesmo algoritmo do generate_manifest.py)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(manifest_path: Path) -> int:
    """Executa a verificacao de integridade e imprime o resultado."""

    if not manifest_path.is_file():
        print(f"ERRO: manifest nao encontrado em {manifest_path}", file=sys.stderr)
        return 1

    with manifest_path.open() as f:
        manifest = json.load(f)

    # A base_path no manifest e relativa ao cwd (onde o script foi chamado).
    base_path = Path(manifest["base_path"])
    allowed_exts = [e.lower() for e in manifest["allowed_extensions"]]
    listed_entries = manifest["files"]

    # Indice { path: sha256 } pra lookup rapido durante a comparacao.
    listed_map = {entry["path"]: entry["sha256"] for entry in listed_entries}

    modificados = []
    removidos = []

    # (1) Percorre o que esta LISTADO no manifest e confere com o disco
    for entry in listed_entries:
        file_on_disk = base_path / entry["path"]

        if not file_on_disk.exists():
            removidos.append(entry["path"])
            continue

        actual_hash = sha256_of_file(file_on_disk)
        if actual_hash != entry["sha256"]:
            modificados.append(entry["path"])

    # (2) Percorre o disco pra ver se ha arquivos NAO listados (backdoor injetado)
    nao_registrados = []
    if base_path.is_dir():
        for file_on_disk in sorted(base_path.rglob("*")):
            if not file_on_disk.is_file():
                continue
            if file_on_disk.suffix.lower() not in allowed_exts:
                continue

            relative = file_on_disk.relative_to(base_path).as_posix()
            if relative not in listed_map:
                nao_registrados.append(relative)

    # Reporta o resultado
    total_ok = len(listed_entries) - len(modificados) - len(removidos)
    print(f"Manifest: {manifest_path}")
    print(f"  Base:              {base_path}")
    print(f"  Arquivos listados: {len(listed_entries)}")
    print(f"  OK:                {total_ok}")
    print(f"  MODIFICADOS:       {len(modificados)}")
    print(f"  REMOVIDOS:         {len(removidos)}")
    print(f"  NAO REGISTRADOS:   {len(nao_registrados)}")

    if modificados:
        print("\nARQUIVOS MODIFICADOS (hash divergiu):")
        for p in modificados:
            print(f"  ~ {p}")
    if removidos:
        print("\nARQUIVOS REMOVIDOS (listados no manifest, sumiram do disco):")
        for p in removidos:
            print(f"  - {p}")
    if nao_registrados:
        print("\nARQUIVOS NAO REGISTRADOS (no disco, ausentes do manifest):")
        for p in nao_registrados:
            print(f"  + {p}")

    if modificados or removidos or nao_registrados:
        print("\nFALHA: manifest nao bate com o disco.")
        return 1

    print("\nOK: todos batem.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica integridade dos arquivos contra o manifest (Pod D3 · Trust Layer)."
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default=Path("security/manifest.json"),
        type=Path,
        help="Caminho do manifest (default: security/manifest.json)",
    )
    args = parser.parse_args()

    return verify(args.manifest)


if __name__ == "__main__":
    sys.exit(main())
