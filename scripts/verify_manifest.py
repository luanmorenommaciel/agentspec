#!/usr/bin/env python3
"""
verify_manifest.py — Verifica que os arquivos batem com o manifest.

Materializa o passo 4 (VERIFICAR) do trust layer, na parte de checagem de
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
        print(f"ERROR: manifest not found at {manifest_path}", file=sys.stderr)
        return 1

    with manifest_path.open() as f:
        manifest = json.load(f)

    # A base_path no manifest e relativa ao cwd (onde o script foi chamado).
    base_path = Path(manifest["base_path"])
    allowed_exts = [e.lower() for e in manifest["allowed_extensions"]]
    listed_entries = manifest["files"]

    # Indice { path: sha256 } pra lookup rapido durante a comparacao.
    listed_map = {entry["path"]: entry["sha256"] for entry in listed_entries}

    modified = []
    removed = []

    # (1) Percorre o que esta LISTADO no manifest e confere com o disco
    for entry in listed_entries:
        file_on_disk = base_path / entry["path"]

        if not file_on_disk.exists():
            removed.append(entry["path"])
            continue

        actual_hash = sha256_of_file(file_on_disk)
        if actual_hash != entry["sha256"]:
            modified.append(entry["path"])

    # (2) Percorre o disco pra ver se ha arquivos NAO listados (backdoor injetado)
    unregistered = []
    if base_path.is_dir():
        for file_on_disk in sorted(base_path.rglob("*")):
            if not file_on_disk.is_file():
                continue
            if file_on_disk.suffix.lower() not in allowed_exts:
                continue

            relative = file_on_disk.relative_to(base_path).as_posix()
            if relative not in listed_map:
                unregistered.append(relative)

    # Reporta o resultado
    total_ok = len(listed_entries) - len(modified) - len(removed)
    print(f"Manifest: {manifest_path}")
    print(f"  Base:          {base_path}")
    print(f"  Files listed:  {len(listed_entries)}")
    print(f"  OK:            {total_ok}")
    print(f"  MODIFIED:      {len(modified)}")
    print(f"  REMOVED:       {len(removed)}")
    print(f"  UNREGISTERED:  {len(unregistered)}")

    if modified:
        print("\nMODIFIED FILES (hash mismatch):")
        for p in modified:
            print(f"  ~ {p}")
    if removed:
        print("\nREMOVED FILES (listed in manifest, missing from disk):")
        for p in removed:
            print(f"  - {p}")
    if unregistered:
        print("\nUNREGISTERED FILES (on disk, absent from manifest):")
        for p in unregistered:
            print(f"  + {p}")

    if modified or removed or unregistered:
        print("\nFAILURE: manifest does not match disk.")
        return 1

    print("\nOK: all files match.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica integridade dos arquivos contra o manifest (Trust Layer)."
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default=Path("plugin/security/manifest.json"),
        type=Path,
        help="Caminho do manifest (default: plugin/security/manifest.json)",
    )
    args = parser.parse_args()

    return verify(args.manifest)


if __name__ == "__main__":
    sys.exit(main())
