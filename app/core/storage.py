from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import UploadFile

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_upload_path(tipo: str, filename: str) -> Path:
    folder = UPLOAD_DIR / tipo
    folder.mkdir(parents=True, exist_ok=True)
    return folder / filename


async def save_upload(file: UploadFile, tipo: str) -> tuple[str, str, int]:
    """Salva il file e restituisce (file_path, checksum, dimensione_bytes)."""
    content = await file.read()
    checksum = hashlib.sha256(content).hexdigest()
    filename = f"{checksum[:16]}_{file.filename}"
    file_path = get_upload_path(tipo, filename)

    with file_path.open("wb") as f:
        f.write(content)

    return str(file_path), checksum, len(content)


def file_exists(file_path: str) -> bool:
    """True se il file referenziato esiste ancora sul disco."""
    return Path(file_path).is_file()


def delete_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()
    # Rimuove la cartella del tipo se è rimasta vuota, per evitare debris.
    parent = path.parent
    if parent != UPLOAD_DIR and parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()


def validate_pdf(content: bytes) -> bool:
    """Verifica che il file sia un PDF valido controllando il magic number."""
    return content[:4] == b"%PDF"
