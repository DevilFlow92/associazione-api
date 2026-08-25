from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_persona(client: AsyncClient, banda_codice: int = 1) -> dict:
    response = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": banda_codice, "nome": "Luigi", "cognome": "Verdi"},
    )
    return response.json()


def allievo_payload(persona_id: int, **overrides) -> dict:
    payload = {
        "persona_id": persona_id,
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
    assert data["codice_allievo"] == "00001"


@pytest.mark.asyncio
async def test_create_allievo_codice_client_ignorato(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/allievi/",
        json=allievo_payload(persona["id"], codice_allievo="ZZZZZ"),
    )
    assert response.status_code == 201
    assert response.json()["codice_allievo"] == "00001"


@pytest.mark.asyncio
async def test_create_allievo_sequenza_incrementale(client: AsyncClient):
    persona1 = await create_persona(client)
    persona2 = await create_persona(client)
    primo = await client.post("/api/v1/allievi/", json=allievo_payload(persona1["id"]))
    secondo = await client.post(
        "/api/v1/allievi/", json=allievo_payload(persona2["id"])
    )
    assert primo.json()["codice_allievo"] == "00001"
    assert secondo.json()["codice_allievo"] == "00002"


@pytest.mark.asyncio
async def test_create_allievo_colma_buco_nella_sequenza(client: AsyncClient):
    persone = [await create_persona(client) for _ in range(3)]
    creati = [
        await client.post("/api/v1/allievi/", json=allievo_payload(p["id"]))
        for p in persone
    ]
    assert [c.json()["codice_allievo"] for c in creati] == ["00001", "00002", "00003"]

    delete_response = await client.delete(f"/api/v1/allievi/{creati[1].json()['id']}")
    assert delete_response.status_code == 204

    persona4 = await create_persona(client)
    quarto = await client.post("/api/v1/allievi/", json=allievo_payload(persona4["id"]))
    assert quarto.json()["codice_allievo"] == "00002"


@pytest.mark.asyncio
async def test_create_allievo_bande_diverse_ripartono_da_zero(client: AsyncClient):
    persona_banda_1a = await create_persona(client, banda_codice=1)
    persona_banda_1b = await create_persona(client, banda_codice=1)
    persona_banda_2 = await create_persona(client, banda_codice=2)

    await client.post("/api/v1/allievi/", json=allievo_payload(persona_banda_1a["id"]))
    secondo_banda_1 = await client.post(
        "/api/v1/allievi/", json=allievo_payload(persona_banda_1b["id"])
    )
    primo_banda_2 = await client.post(
        "/api/v1/allievi/", json=allievo_payload(persona_banda_2["id"])
    )

    assert secondo_banda_1.json()["codice_allievo"] == "00002"
    assert primo_banda_2.json()["codice_allievo"] == "00001"


@pytest.mark.asyncio
async def test_create_allievo_persona_not_found(client: AsyncClient):
    response = await client.post("/api/v1/allievi/", json=allievo_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_allievo_persona_already_linked(client: AsyncClient):
    persona = await create_persona(client)
    await client.post("/api/v1/allievi/", json=allievo_payload(persona["id"]))
    response = await client.post(
        "/api/v1/allievi/", json=allievo_payload(persona["id"])
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
async def test_update_allievo_codice_duplicato(client: AsyncClient):
    persona1 = await create_persona(client)
    persona2 = await create_persona(client)
    primo = await client.post("/api/v1/allievi/", json=allievo_payload(persona1["id"]))
    secondo = await client.post(
        "/api/v1/allievi/", json=allievo_payload(persona2["id"])
    )
    response = await client.patch(
        f"/api/v1/allievi/{secondo.json()['id']}",
        json={"codice_allievo": primo.json()["codice_allievo"]},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_allievo_codice_troppo_lungo(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/allievi/", json=allievo_payload(persona["id"]))
    response = await client.patch(
        f"/api/v1/allievi/{created.json()['id']}",
        json={"codice_allievo": "000001"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_allievo(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/allievi/", json=allievo_payload(persona["id"]))
    allievo_id = created.json()["id"]
    response = await client.delete(f"/api/v1/allievi/{allievo_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/allievi/{allievo_id}")
    assert response.status_code == 404
