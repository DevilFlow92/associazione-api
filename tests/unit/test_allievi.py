from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_persona(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": "Luigi", "cognome": "Verdi"},
    )
    return response.json()


def allievo_payload(persona_id: int, **overrides) -> dict:
    payload = {
        "persona_id": persona_id,
        "codice_allievo": "A001",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_allievo(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/allievi/", json=allievo_payload(persona["id"])
    )
    assert response.status_code == 201
    data = response.json()
    assert data["persona_id"] == persona["id"]
    assert data["codice_allievo"] == "A001"


@pytest.mark.asyncio
async def test_create_allievo_codice_esatto_5_caratteri(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/allievi/",
        json=allievo_payload(persona["id"], codice_allievo="A0012"),
    )
    assert response.status_code == 201
    assert response.json()["codice_allievo"] == "A0012"


@pytest.mark.asyncio
async def test_create_allievo_codice_troppo_lungo(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/allievi/",
        json=allievo_payload(persona["id"], codice_allievo="A00123"),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_allievo_persona_not_found(client: AsyncClient):
    response = await client.post("/api/v1/allievi/", json=allievo_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_allievo_duplicate_codice(client: AsyncClient):
    persona1 = await create_persona(client)
    persona2 = await create_persona(client)
    await client.post("/api/v1/allievi/", json=allievo_payload(persona1["id"]))
    response = await client.post(
        "/api/v1/allievi/", json=allievo_payload(persona2["id"])
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_allievo_persona_already_linked(client: AsyncClient):
    persona = await create_persona(client)
    await client.post("/api/v1/allievi/", json=allievo_payload(persona["id"]))
    response = await client.post(
        "/api/v1/allievi/",
        json=allievo_payload(persona["id"], codice_allievo="A002"),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_allievo_not_found(client: AsyncClient):
    response = await client.get("/api/v1/allievi/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_allievi_empty(client: AsyncClient):
    response = await client.get("/api/v1/allievi/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0
    assert data["meta"]["page"] == 1


@pytest.mark.asyncio
async def test_update_allievo(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/allievi/", json=allievo_payload(persona["id"]))
    allievo_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/allievi/{allievo_id}", json={"codice_allievo": "A099"}
    )
    assert response.status_code == 200
    assert response.json()["codice_allievo"] == "A099"


@pytest.mark.asyncio
async def test_delete_allievo(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/allievi/", json=allievo_payload(persona["id"]))
    allievo_id = created.json()["id"]
    response = await client.delete(f"/api/v1/allievi/{allievo_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/allievi/{allievo_id}")
    assert response.status_code == 404
