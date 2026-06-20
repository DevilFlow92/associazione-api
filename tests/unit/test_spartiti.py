from __future__ import annotations

import pytest
from httpx import AsyncClient


def pdf_file(filename: str = "spartito.pdf") -> tuple[str, tuple[str, bytes, str]]:
    return ("file", (filename, b"%PDF-1.4 spartito", "application/pdf"))


async def upload_documento(client: AsyncClient, filename: str = "s.pdf") -> dict:
    response = await client.post("/api/v1/documenti/", files=[pdf_file(filename)])
    assert response.status_code == 201
    return response.json()


def spartito_payload(tipo_spartito_codice: int, documento_id: int, **overrides) -> dict:
    payload = {
        "banda_codice": 1,
        "tipo_spartito_codice": tipo_spartito_codice,
        "documento_id": documento_id,
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_spartito(client: AsyncClient):
    doc = await upload_documento(client)
    response = await client.post(
        "/api/v1/spartiti/",
        json=spartito_payload(1, doc["id"]),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tipo_spartito_codice"] == 1
    assert data["documento_id"] == doc["id"]
    assert data["strumento_codice"] is None


@pytest.mark.asyncio
async def test_create_spartito_con_strumento_e_collocazione(client: AsyncClient):
    doc = await upload_documento(client)
    response = await client.post(
        "/api/v1/spartiti/",
        json=spartito_payload(
            2,
            doc["id"],
            strumento_codice=5,
            scaffale="A",
            ripiano="3",
            cartella="Inni",
        ),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["strumento_codice"] == 5
    assert data["scaffale"] == "A"
    assert data["ripiano"] == "3"
    assert data["cartella"] == "Inni"


@pytest.mark.asyncio
async def test_get_spartito_not_found(client: AsyncClient):
    response = await client.get("/api/v1/spartiti/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_spartiti_empty(client: AsyncClient):
    response = await client.get("/api/v1/spartiti/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_list_spartiti_filtro_tipo(client: AsyncClient):
    doc1 = await upload_documento(client, "d1.pdf")
    doc2 = await upload_documento(client, "d2.pdf")
    await client.post("/api/v1/spartiti/", json=spartito_payload(1, doc1["id"]))
    await client.post("/api/v1/spartiti/", json=spartito_payload(2, doc2["id"]))
    response = await client.get("/api/v1/spartiti/?tipo_spartito_codice=1")
    assert response.json()["meta"]["total_items"] == 1


@pytest.mark.asyncio
async def test_update_spartito(client: AsyncClient):
    doc = await upload_documento(client)
    created = await client.post(
        "/api/v1/spartiti/", json=spartito_payload(1, doc["id"])
    )
    spartito_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/spartiti/{spartito_id}",
        json={"scaffale": "B", "ripiano": "1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scaffale"] == "B"
    assert data["ripiano"] == "1"


@pytest.mark.asyncio
async def test_delete_spartito(client: AsyncClient):
    doc = await upload_documento(client)
    created = await client.post(
        "/api/v1/spartiti/", json=spartito_payload(1, doc["id"])
    )
    spartito_id = created.json()["id"]
    response = await client.delete(f"/api/v1/spartiti/{spartito_id}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/spartiti/{spartito_id}")).status_code == 404
