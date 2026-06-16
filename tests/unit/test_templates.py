from __future__ import annotations

import os

import pytest
from httpx import AsyncClient


def pdf_file(filename: str = "template.pdf") -> tuple[str, tuple[str, bytes, str]]:
    content = b"%PDF-1.4 test template content"
    return ("file", (filename, content, "application/pdf"))


async def upload_documento(client: AsyncClient, filename: str = "doc.pdf") -> dict:
    response = await client.post("/api/v1/documenti/", files=[pdf_file(filename)])
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_create_template(client: AsyncClient):
    doc = await upload_documento(client)
    response = await client.post(
        "/api/v1/templates/",
        json={"documento_id": doc["id"], "nome": "Modulo Test"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["documento_id"] == doc["id"]
    assert data["nome"] == "Modulo Test"
    assert data["descrizione"] is None
    assert "creato_il" in data


@pytest.mark.asyncio
async def test_create_template_con_descrizione(client: AsyncClient):
    doc = await upload_documento(client)
    response = await client.post(
        "/api/v1/templates/",
        json={
            "documento_id": doc["id"],
            "nome": "Ricevuta Base",
            "descrizione": "Template per le ricevute ai soci",
        },
    )
    assert response.status_code == 201
    assert response.json()["descrizione"] == "Template per le ricevute ai soci"


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


@pytest.mark.asyncio
async def test_list_templates_filtro_documento(client: AsyncClient):
    doc1 = await upload_documento(client, "d1.pdf")
    doc2 = await upload_documento(client, "d2.pdf")
    await client.post(
        "/api/v1/templates/", json={"documento_id": doc1["id"], "nome": "T1"}
    )
    await client.post(
        "/api/v1/templates/", json={"documento_id": doc2["id"], "nome": "T2"}
    )
    response = await client.get(f"/api/v1/templates/?documento_id={doc1['id']}")
    assert response.json()["meta"]["total_items"] == 1


@pytest.mark.asyncio
async def test_update_template(client: AsyncClient):
    doc = await upload_documento(client)
    created = await client.post(
        "/api/v1/templates/",
        json={"documento_id": doc["id"], "nome": "Originale"},
    )
    template_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/templates/{template_id}",
        json={"nome": "Aggiornato", "descrizione": "Nuova desc"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Aggiornato"
    assert data["descrizione"] == "Nuova desc"


@pytest.mark.asyncio
async def test_delete_template(client: AsyncClient):
    doc = await upload_documento(client)
    created = await client.post(
        "/api/v1/templates/", json={"documento_id": doc["id"], "nome": "Da cancellare"}
    )
    template_id = created.json()["id"]
    response = await client.delete(f"/api/v1/templates/{template_id}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/templates/{template_id}")).status_code == 404


@pytest.mark.asyncio
async def test_download_template(client: AsyncClient):
    doc = await upload_documento(client, "scaricabile.pdf")
    created = await client.post(
        "/api/v1/templates/", json={"documento_id": doc["id"], "nome": "Scaricabile"}
    )
    template_id = created.json()["id"]
    response = await client.get(f"/api/v1/templates/{template_id}/download")
    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 test template content"


@pytest.mark.asyncio
async def test_download_template_missing_file(client: AsyncClient):
    doc = await upload_documento(client, "fantasma.pdf")
    created = await client.post(
        "/api/v1/templates/", json={"documento_id": doc["id"], "nome": "Fantasma"}
    )
    os.remove(doc["file_path"])
    response = await client.get(f"/api/v1/templates/{created.json()['id']}/download")
    assert response.status_code == 404
