from __future__ import annotations

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
        "/api/v1/documenti/?tipo=modulo_iscrizione",
        files=[pdf_file()],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tipo"] == "modulo_iscrizione"
    assert data["mime_type"] == "application/pdf"
    assert "checksum" in data


@pytest.mark.asyncio
async def test_upload_documento_non_pdf(client: AsyncClient):
    response = await client.post(
        "/api/v1/documenti/?tipo=modulo_iscrizione",
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
async def test_delete_documento(client: AsyncClient):
    upload = await client.post(
        "/api/v1/documenti/?tipo=partitura",
        files=[pdf_file("partitura.pdf")],
    )
    doc_id = upload.json()["id"]
    response = await client.delete(f"/api/v1/documenti/{doc_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/documenti/{doc_id}")
    assert response.status_code == 404
