"""Storage backends for uploaded files.

Set the STORAGE_BACKEND environment variable to choose a backend:

  STORAGE_BACKEND=local  (default)
      Files are stored on the local filesystem under uploads/.

  STORAGE_BACKEND=r2
      Files are stored in a Cloudflare R2 bucket via the S3-compatible API.
      Requires: R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
                R2_BUCKET_NAME environment variables.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import UploadFile


class Storage(ABC):
    @abstractmethod
    async def save(
        self, content: bytes, tipo: str, filename: str
    ) -> tuple[str, str, int]:
        """Persist content and return (path_or_key, sha256_checksum, size_bytes)."""

    @abstractmethod
    async def delete(self, path: str) -> None: ...

    @abstractmethod
    async def exists(self, path: str) -> bool: ...

    @abstractmethod
    async def get_bytes(self, path: str) -> bytes: ...


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class LocalStorage(Storage):
    def __init__(self, base_dir: Path = UPLOAD_DIR) -> None:
        self._base = base_dir

    def _path(self, tipo: str, filename: str) -> Path:
        folder = self._base / tipo
        folder.mkdir(parents=True, exist_ok=True)
        return folder / filename

    async def save(
        self, content: bytes, tipo: str, filename: str
    ) -> tuple[str, str, int]:
        checksum = hashlib.sha256(content).hexdigest()
        dest = self._path(tipo, f"{checksum[:16]}_{filename}")
        dest.write_bytes(content)
        return str(dest), checksum, len(content)

    async def delete(self, path: str) -> None:
        p = Path(path)
        if p.exists():
            p.unlink()
        parent = p.parent
        if parent != self._base and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()

    async def exists(self, path: str) -> bool:
        return Path(path).is_file()

    async def get_bytes(self, path: str) -> bytes:
        return Path(path).read_bytes()


class R2Storage(Storage):
    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._bucket_name = bucket_name

    def _client(self):  # type: ignore[return]
        import boto3  # lazy import — only required when R2 is active

        return boto3.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
        )

    async def save(
        self, content: bytes, tipo: str, filename: str
    ) -> tuple[str, str, int]:
        checksum = hashlib.sha256(content).hexdigest()
        key = f"{tipo}/{checksum[:16]}_{filename}"
        client = self._client()
        await asyncio.to_thread(
            client.put_object, Bucket=self._bucket_name, Key=key, Body=content
        )
        return key, checksum, len(content)

    async def delete(self, path: str) -> None:
        client = self._client()
        await asyncio.to_thread(
            client.delete_object, Bucket=self._bucket_name, Key=path
        )

    async def exists(self, path: str) -> bool:
        import botocore.exceptions  # lazy import alongside boto3

        client = self._client()
        try:
            await asyncio.to_thread(
                client.head_object, Bucket=self._bucket_name, Key=path
            )
            return True
        except botocore.exceptions.ClientError as exc:
            if exc.response["Error"]["Code"] == "404":
                return False
            raise

    async def get_bytes(self, path: str) -> bytes:
        client = self._client()
        response = await asyncio.to_thread(
            client.get_object, Bucket=self._bucket_name, Key=path
        )
        return await asyncio.to_thread(response["Body"].read)


def get_storage() -> Storage:
    backend = os.environ.get("STORAGE_BACKEND", "local").lower()
    if backend == "local":
        return LocalStorage()
    if backend == "r2":
        return R2Storage(
            endpoint_url=os.environ["R2_ENDPOINT_URL"],
            access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            bucket_name=os.environ["R2_BUCKET_NAME"],
        )
    raise ValueError(f"Unknown STORAGE_BACKEND: {backend!r}")


storage: Storage = get_storage()


# ── Public shims (imported by name across the codebase) ──────────────────────


async def save_upload(file: UploadFile, tipo: str) -> tuple[str, str, int]:
    content = await file.read()
    return await storage.save(content, tipo, file.filename or "upload")


async def file_exists(file_path: str) -> bool:
    return await storage.exists(file_path)


async def delete_file(file_path: str) -> None:
    await storage.delete(file_path)


def validate_pdf(content: bytes) -> bool:
    """Verifica che il file sia un PDF valido controllando il magic number."""
    return content[:4] == b"%PDF"
