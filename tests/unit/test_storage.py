from __future__ import annotations

import hashlib
import inspect
from pathlib import Path

import pytest
import pytest_asyncio

from app.core.storage import LocalStorage


@pytest_asyncio.fixture
async def local_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> LocalStorage:
    import app.core.storage as storage_module

    monkeypatch.setattr(storage_module, "UPLOAD_DIR", tmp_path)
    return LocalStorage(base_dir=tmp_path)


PDF_CONTENT = b"%PDF-1.4 test content"
TIPO = "documenti"
FILENAME = "sample.pdf"


@pytest.mark.asyncio
async def test_save_creates_file(local_storage: LocalStorage, tmp_path: Path) -> None:
    file_path, checksum, _ = await local_storage.save(PDF_CONTENT, TIPO, FILENAME)
    assert Path(file_path).is_file()
    assert checksum == hashlib.sha256(PDF_CONTENT).hexdigest()


@pytest.mark.asyncio
async def test_save_returns_correct_size(local_storage: LocalStorage) -> None:
    _, _, size = await local_storage.save(PDF_CONTENT, TIPO, FILENAME)
    assert size == len(PDF_CONTENT)


@pytest.mark.asyncio
async def test_exists_true(local_storage: LocalStorage) -> None:
    file_path, _, _ = await local_storage.save(PDF_CONTENT, TIPO, FILENAME)
    assert await local_storage.exists(file_path) is True


@pytest.mark.asyncio
async def test_exists_false(local_storage: LocalStorage, tmp_path: Path) -> None:
    assert await local_storage.exists(str(tmp_path / "nonexistent.pdf")) is False


@pytest.mark.asyncio
async def test_delete_removes_file(local_storage: LocalStorage) -> None:
    file_path, _, _ = await local_storage.save(PDF_CONTENT, TIPO, FILENAME)
    await local_storage.delete(file_path)
    assert await local_storage.exists(file_path) is False


@pytest.mark.asyncio
async def test_delete_prunes_empty_dir(
    local_storage: LocalStorage, tmp_path: Path
) -> None:
    file_path, _, _ = await local_storage.save(PDF_CONTENT, TIPO, FILENAME)
    parent = Path(file_path).parent
    assert parent.is_dir()
    await local_storage.delete(file_path)
    assert not parent.exists()


@pytest.mark.asyncio
async def test_get_bytes_roundtrip(local_storage: LocalStorage) -> None:
    file_path, _, _ = await local_storage.save(PDF_CONTENT, TIPO, FILENAME)
    retrieved = await local_storage.get_bytes(file_path)
    assert retrieved == PDF_CONTENT


@pytest.mark.asyncio
async def test_save_deduplicates_by_checksum(local_storage: LocalStorage) -> None:
    path1, _, _ = await local_storage.save(PDF_CONTENT, TIPO, FILENAME)
    path2, _, _ = await local_storage.save(PDF_CONTENT, TIPO, FILENAME)
    assert path1 == path2


def test_legacy_shims_are_coroutines() -> None:
    from app.core.storage import delete_file, file_exists, save_upload

    assert inspect.iscoroutinefunction(save_upload)
    assert inspect.iscoroutinefunction(file_exists)
    assert inspect.iscoroutinefunction(delete_file)
