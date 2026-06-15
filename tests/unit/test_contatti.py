from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_persona(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": "Mario", "cognome": "Rossi"},
    )
    return response.json()


def contatto_payload(persona_id: int, **overrides) -> dict:
    payload = {
        "persona_id": persona_id,
        "ruolo_contatto_codice": 1,
        "email": "mario.rossi@test.com",
        "telefono": "070123456",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_contatto(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/contatti/", json=contatto_payload(persona["id"])
    )
    assert response.status_code == 201
    data = response.json()
    assert data["persona_id"] == persona["id"]
    assert data["email"] == "mario.rossi@test.com"


@pytest.mark.asyncio
async def test_create_contatto_persona_not_found(client: AsyncClient):
    response = await client.post("/api/v1/contatti/", json=contatto_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_contatto_not_found(client: AsyncClient):
    response = await client.get("/api/v1/contatti/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_contatti_persona(client: AsyncClient):
    persona = await create_persona(client)
    await client.post("/api/v1/contatti/", json=contatto_payload(persona["id"]))
    await client.post(
        "/api/v1/contatti/",
        json=contatto_payload(persona["id"], ruolo_contatto_codice=2),
    )
    response = await client.get(f"/api/v1/contatti/persona/{persona['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 2


@pytest.mark.asyncio
async def test_get_contatti_persona_not_found(client: AsyncClient):
    response = await client.get("/api/v1/contatti/persona/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_contatto(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post(
        "/api/v1/contatti/", json=contatto_payload(persona["id"])
    )
    contatto_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/contatti/{contatto_id}", json={"telefono": "070999999"}
    )
    assert response.status_code == 200
    assert response.json()["telefono"] == "070999999"


@pytest.mark.asyncio
async def test_delete_contatto(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post(
        "/api/v1/contatti/", json=contatto_payload(persona["id"])
    )
    contatto_id = created.json()["id"]
    response = await client.delete(f"/api/v1/contatti/{contatto_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/contatti/{contatto_id}")
    assert response.status_code == 404
