from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_persona(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": "Mario", "cognome": "Rossi"},
    )
    return response.json()


def socio_payload(persona_id: int, **overrides) -> dict:
    payload = {
        "persona_id": persona_id,
        "codice_socio": "S001",
        "banda_codice": 1,
        "ruolo_banda_codice": 10,
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_socio(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    assert response.status_code == 201
    data = response.json()
    assert data["persona_id"] == persona["id"]
    assert data["codice_socio"] == "S001"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_socio_persona_not_found(client: AsyncClient):
    response = await client.post("/api/v1/soci/", json=socio_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_socio_duplicate_codice(client: AsyncClient):
    persona = await create_persona(client)
    await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    response = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_socio_not_found(client: AsyncClient):
    response = await client.get("/api/v1/soci/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_soci_empty(client: AsyncClient):
    response = await client.get("/api/v1/soci/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0
    assert data["meta"]["page"] == 1


@pytest.mark.asyncio
async def test_update_socio(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    socio_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/soci/{socio_id}", json={"ruolo_banda_codice": 1}
    )
    assert response.status_code == 200
    assert response.json()["ruolo_banda_codice"] == 1


@pytest.mark.asyncio
async def test_delete_socio(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    socio_id = created.json()["id"]
    response = await client.delete(f"/api/v1/soci/{socio_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/soci/{socio_id}")
    assert response.status_code == 404
