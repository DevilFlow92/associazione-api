from __future__ import annotations

import os

import pytest
from httpx import AsyncClient


def pdf_file(filename: str = "template.pdf") -> tuple[str, tuple[str, bytes, str]]:
    content = b"%PDF-1.4 test template content"
    return ("file", (filename, content, "application/pdf"))


def fake_file(filename: str = "test.txt") -> tuple[str, tuple[str, bytes, str]]:
    return ("file", (filename, b"not a pdf", "text/plain"))


@pytest.mark.asyncio
async def test_upload_template(client: AsyncClient):
    response = await client.post(
        "/api/v1/templates/?tipo=modulo_iscrizione&nome=Modulo%20Test",
        files=[pdf_file()],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Modulo Test"
    assert data["tipo"] == "modulo_iscrizione"
    assert data["attivo"] is True
    assert "checksum" in data


@pytest.mark.asyncio
async def test_upload_template_non_pdf(client: AsyncClient):
    response = await client.post(
        "/api/v1/templates/?tipo=modulo_iscrizione&nome=Test",
        files=[fake_file()],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_template_not_found(client: AsyncClient):
    response = await client.get("/api/v1/templates/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_templates_empty(client: AsyncClient):
    response = await client.get("/api/v1/templates/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0
    assert data["meta"]["page"] == 1


@pytest.mark.asyncio
async def test_update_template(client: AsyncClient):
    upload = await client.post(
        "/api/v1/templates/?tipo=ricevuta&nome=Ricevuta%20Base",
        files=[pdf_file("ricevuta.pdf")],
    )
    template_id = upload.json()["id"]
    response = await client.patch(
        f"/api/v1/templates/{template_id}",
        json={"nome": "Ricevuta Aggiornata", "attivo": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Ricevuta Aggiornata"
    assert data["attivo"] is False


@pytest.mark.asyncio
async def test_delete_template(client: AsyncClient):
    upload = await client.post(
        "/api/v1/templates/?tipo=altro&nome=Da%20Cancellare",
        files=[pdf_file()],
    )
    template_id = upload.json()["id"]
    response = await client.delete(f"/api/v1/templates/{template_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/templates/{template_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_template(client: AsyncClient):
    upload = await client.post(
        "/api/v1/templates/?tipo=altro&nome=Scaricabile",
        files=[pdf_file()],
    )
    template_id = upload.json()["id"]
    response = await client.get(f"/api/v1/templates/{template_id}/download")
    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 test template content"


@pytest.mark.asyncio
async def test_download_template_missing_file(client: AsyncClient):
    upload = await client.post(
        "/api/v1/templates/?tipo=altro&nome=Fantasma",
        files=[pdf_file()],
    )
    data = upload.json()
    os.remove(data["file_path"])  # il file sparisce ma la riga DB resta
    response = await client.get(f"/api/v1/templates/{data['id']}/download")
    assert response.status_code == 404
