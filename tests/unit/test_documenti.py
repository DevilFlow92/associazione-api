from __future__ import annotations

import os

import pytest
from httpx import AsyncClient


def pdf_file(filename: str = "test.pdf") -> tuple[str, tuple[str, bytes, str]]:
    content = b"%PDF-1.4 test pdf content"
    return ("file", (filename, content, "application/pdf"))


def fake_file(filename: str = "test.txt") -> tuple[str, tuple[str, bytes, str]]:
    return ("file", (filename, b"not a pdf", "text/plain"))


@pytest.mark.asyncio
async def test_upload_documento(client: AsyncClient):
    response = await client.post(
        "/api/v1/documenti/",
        files=[pdf_file()],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["mime_type"] == "application/pdf"
    assert "checksum" in data
    assert data["tipo_documento_codice"] is None


@pytest.mark.asyncio
async def test_upload_documento_con_tipo(client: AsyncClient):
    response = await client.post(
        "/api/v1/documenti/?tipo_documento_codice=3",
        files=[pdf_file()],
    )
    assert response.status_code == 201
    assert response.json()["tipo_documento_codice"] == 3


@pytest.mark.asyncio
async def test_upload_documento_non_pdf(client: AsyncClient):
    response = await client.post(
        "/api/v1/documenti/",
        files=[fake_file()],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_documento_not_found(client: AsyncClient):
    response = await client.get("/api/v1/documenti/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_documenti_empty(client: AsyncClient):
    response = await client.get("/api/v1/documenti/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0
    assert data["meta"]["page"] == 1


@pytest.mark.asyncio
async def test_list_documenti_filtro_tipo(client: AsyncClient):
    await client.post(
        "/api/v1/documenti/?tipo_documento_codice=1", files=[pdf_file("a.pdf")]
    )
    await client.post(
        "/api/v1/documenti/?tipo_documento_codice=3", files=[pdf_file("b.pdf")]
    )
    response = await client.get("/api/v1/documenti/?tipo_documento_codice=1")
    assert response.json()["meta"]["total_items"] == 1


@pytest.mark.asyncio
async def test_delete_documento(client: AsyncClient):
    upload = await client.post("/api/v1/documenti/", files=[pdf_file("del.pdf")])
    doc_id = upload.json()["id"]
    response = await client.delete(f"/api/v1/documenti/{doc_id}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/documenti/{doc_id}")).status_code == 404


@pytest.mark.asyncio
async def test_download_documento(client: AsyncClient):
    upload = await client.post(
        "/api/v1/documenti/", files=[pdf_file("scaricabile.pdf")]
    )
    doc_id = upload.json()["id"]
    response = await client.get(f"/api/v1/documenti/{doc_id}/download")
    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 test pdf content"


@pytest.mark.asyncio
async def test_preview_documento_inline(client: AsyncClient):
    upload = await client.post("/api/v1/documenti/", files=[pdf_file("anteprima.pdf")])
    doc_id = upload.json()["id"]
    response = await client.get(f"/api/v1/documenti/{doc_id}/preview")
    assert response.status_code == 200
    assert response.headers["content-disposition"].lower().startswith("inline")


@pytest.mark.asyncio
async def test_preview_documento_not_found(client: AsyncClient):
    response = await client.get("/api/v1/documenti/999/preview")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_documento_missing_file(client: AsyncClient):
    upload = await client.post("/api/v1/documenti/", files=[pdf_file("fantasma.pdf")])
    data = upload.json()
    os.remove(data["file_path"])
    response = await client.get(f"/api/v1/documenti/{data['id']}/download")
    assert response.status_code == 404
