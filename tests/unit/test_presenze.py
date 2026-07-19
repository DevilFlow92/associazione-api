from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_persona(client: AsyncClient, **overrides) -> dict:
    payload = {"banda_codice": 1, "nome": "Mario", "cognome": "Rossi"}
    payload.update(overrides)
    response = await client.post("/api/v1/persone/", json=payload)
    return response.json()


async def create_indirizzo(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/indirizzi/",
        json={"tipo_indirizzo_codice": 4, "prima_riga": "Piazza Chiesa"},
    )
    return response.json()


async def create_servizio(client: AsyncClient, **overrides) -> dict:
    indirizzo = await create_indirizzo(client)
    payload = {
        "banda_codice": 1,
        "anno": 2026,
        "descrizione_servizio": "Processione Sant'Antonio",
        "data_servizio": "2026-06-13T18:00:00",
        "indirizzo_id": indirizzo["id"],
    }
    payload.update(overrides)
    response = await client.post("/api/v1/servizi/", json=payload)
    return response.json()


def presenza_payload(persona_id: int, servizio_id: int, **overrides) -> dict:
    payload = {"persona_id": persona_id, "servizio_id": servizio_id}
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_presenza(client: AsyncClient):
    persona = await create_persona(client)
    servizio = await create_servizio(client)
    response = await client.post(
        "/api/v1/presenze/", json=presenza_payload(persona["id"], servizio["id"])
    )
    assert response.status_code == 201
    data = response.json()
    assert data["persona_id"] == persona["id"]
    assert data["servizio_id"] == servizio["id"]
    assert data["stato"] is None


@pytest.mark.asyncio
async def test_create_presenza_persona_not_found(client: AsyncClient):
    servizio = await create_servizio(client)
    response = await client.post(
        "/api/v1/presenze/", json=presenza_payload(999, servizio["id"])
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_presenza_servizio_not_found(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/presenze/", json=presenza_payload(persona["id"], 999)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_presenza_duplicata(client: AsyncClient):
    """Una persona non può comparire due volte nell'organico dello stesso servizio."""
    persona = await create_persona(client)
    servizio = await create_servizio(client)
    await client.post(
        "/api/v1/presenze/", json=presenza_payload(persona["id"], servizio["id"])
    )
    response = await client.post(
        "/api/v1/presenze/", json=presenza_payload(persona["id"], servizio["id"])
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_presenza(client: AsyncClient):
    persona = await create_persona(client)
    servizio = await create_servizio(client)
    created = await client.post(
        "/api/v1/presenze/", json=presenza_payload(persona["id"], servizio["id"])
    )
    presenza_id = created.json()["id"]

    response = await client.delete(f"/api/v1/presenze/{presenza_id}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/presenze/{presenza_id}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_presenza_not_found(client: AsyncClient):
    response = await client.delete("/api/v1/presenze/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_organico_servizio(client: AsyncClient):
    persona1 = await create_persona(client, nome="Mario", cognome="Rossi")
    persona2 = await create_persona(client, nome="Luigi", cognome="Bianchi")
    servizio = await create_servizio(client)
    await client.post(
        "/api/v1/presenze/", json=presenza_payload(persona1["id"], servizio["id"])
    )
    await client.post(
        "/api/v1/presenze/", json=presenza_payload(persona2["id"], servizio["id"])
    )

    response = await client.get(f"/api/v1/presenze/servizio/{servizio['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 2
    nomi = {item["persona"]["nome"] for item in data["items"]}
    assert nomi == {"Mario", "Luigi"}


@pytest.mark.asyncio
async def test_get_organico_servizio_not_found(client: AsyncClient):
    response = await client.get("/api/v1/presenze/servizio/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_presenza_stato(client: AsyncClient):
    persona = await create_persona(client)
    servizio = await create_servizio(client)
    created = await client.post(
        "/api/v1/presenze/", json=presenza_payload(persona["id"], servizio["id"])
    )
    presenza_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/presenze/{presenza_id}",
        json={"stato": "PRESENTE", "note": "Arrivato in orario"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stato"] == "PRESENTE"
    assert data["note"] == "Arrivato in orario"


@pytest.mark.asyncio
async def test_update_presenza_not_found(client: AsyncClient):
    response = await client.patch("/api/v1/presenze/999", json={"stato": "ASSENTE"})
    assert response.status_code == 404
