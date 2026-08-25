from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_persona(client: AsyncClient, banda_codice: int = 1) -> dict:
    response = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": banda_codice, "nome": "Luigi", "cognome": "Verdi"},
    )
    return response.json()


def esterno_payload(persona_id: int, **overrides) -> dict:
    payload = {
        "persona_id": persona_id,
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
    assert data["codice_esterno"] == "00001"
    assert data["strumento_codice"] == 5


@pytest.mark.asyncio
async def test_create_esterno_codice_client_ignorato(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/esterni/",
        json=esterno_payload(persona["id"], codice_esterno="ZZZZZ"),
    )
    assert response.status_code == 201
    assert response.json()["codice_esterno"] == "00001"


@pytest.mark.asyncio
async def test_create_esterno_sequenza_incrementale(client: AsyncClient):
    persona = await create_persona(client)
    primo = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    secondo = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    assert primo.json()["codice_esterno"] == "00001"
    assert secondo.json()["codice_esterno"] == "00002"


@pytest.mark.asyncio
async def test_create_esterno_colma_buco_nella_sequenza(client: AsyncClient):
    persona = await create_persona(client)
    primo = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    secondo = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    terzo = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    assert [
        primo.json()["codice_esterno"],
        secondo.json()["codice_esterno"],
        terzo.json()["codice_esterno"],
    ] == ["00001", "00002", "00003"]

    delete_response = await client.delete(f"/api/v1/esterni/{secondo.json()['id']}")
    assert delete_response.status_code == 204

    quarto = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    assert quarto.json()["codice_esterno"] == "00002"


@pytest.mark.asyncio
async def test_create_esterno_bande_diverse_ripartono_da_zero(client: AsyncClient):
    persona_banda_1 = await create_persona(client, banda_codice=1)
    persona_banda_2 = await create_persona(client, banda_codice=2)

    await client.post("/api/v1/esterni/", json=esterno_payload(persona_banda_1["id"]))
    secondo_banda_1 = await client.post(
        "/api/v1/esterni/", json=esterno_payload(persona_banda_1["id"])
    )
    primo_banda_2 = await client.post(
        "/api/v1/esterni/", json=esterno_payload(persona_banda_2["id"])
    )

    assert secondo_banda_1.json()["codice_esterno"] == "00002"
    assert primo_banda_2.json()["codice_esterno"] == "00001"


@pytest.mark.asyncio
async def test_create_esterno_persona_not_found(client: AsyncClient):
    response = await client.post("/api/v1/esterni/", json=esterno_payload(999))
    assert response.status_code == 404


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
async def test_update_esterno_codice_duplicato(client: AsyncClient):
    persona = await create_persona(client)
    primo = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    secondo = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    response = await client.patch(
        f"/api/v1/esterni/{secondo.json()['id']}",
        json={"codice_esterno": primo.json()["codice_esterno"]},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_esterno_codice_troppo_lungo(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    response = await client.patch(
        f"/api/v1/esterni/{created.json()['id']}",
        json={"codice_esterno": "000001"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_esterno(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/esterni/", json=esterno_payload(persona["id"]))
    esterno_id = created.json()["id"]
    response = await client.delete(f"/api/v1/esterni/{esterno_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/esterni/{esterno_id}")
    assert response.status_code == 404
