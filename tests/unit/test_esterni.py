from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_persona(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": "Luigi", "cognome": "Verdi"},
    )
    return response.json()


def esterno_payload(persona_id: int, **overrides) -> dict:
    payload = {
        "persona_id": persona_id,
        "codice_esterno": "E001",
        "strumento_codice": 5,
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_esterno(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/esterni/", json=esterno_payload(persona["id"])
    )
    assert response.status_code == 201
    data = response.json()
    assert data["persona_id"] == persona["id"]
    assert data["codice_esterno"] == "E001"
    assert data["strumento_codice"] == 5


@pytest.mark.asyncio
async def test_create_esterno_persona_not_found(client: AsyncClient):
    response = await client.post("/api/v1/esterni/", json=esterno_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_esterno_duplicate_codice(client: AsyncClient):
    persona = await create_persona(client)
    await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    response = await client.post(
        "/api/v1/esterni/", json=esterno_payload(persona["id"])
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_esterno_not_found(client: AsyncClient):
    response = await client.get("/api/v1/esterni/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_esterno(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    esterno_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/esterni/{esterno_id}", json={"strumento_codice": 10}
    )
    assert response.status_code == 200
    assert response.json()["strumento_codice"] == 10


@pytest.mark.asyncio
async def test_delete_esterno(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    esterno_id = created.json()["id"]
    response = await client.delete(f"/api/v1/esterni/{esterno_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/esterni/{esterno_id}")
    assert response.status_code == 404
