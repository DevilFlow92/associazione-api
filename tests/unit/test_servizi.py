from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_indirizzo(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/indirizzi/",
        json={"tipo_indirizzo_codice": 4, "prima_riga": "Piazza Chiesa"},
    )
    return response.json()


def servizio_payload(indirizzo_id: int, **overrides) -> dict:
    payload = {
        "banda_codice": 1,
        "anno": 2026,
        "descrizione_servizio": "Processione Sant'Antonio",
        "data_servizio": "2026-06-13T18:00:00",
        "indirizzo_id": indirizzo_id,
    }
    payload.update(overrides)
    return payload


async def create_servizio(client: AsyncClient) -> dict:
    indirizzo = await create_indirizzo(client)
    response = await client.post(
        "/api/v1/servizi/", json=servizio_payload(indirizzo["id"])
    )
    return response.json()


async def create_esterno(client: AsyncClient) -> dict:
    persona = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": "Gino", "cognome": "Esterni"},
    )
    response = await client.post(
        "/api/v1/esterni/",
        json={
            "persona_id": persona.json()["id"],
            "codice_esterno": "E010",
            "strumento_codice": 5,
        },
    )
    return response.json()


@pytest.mark.asyncio
async def test_create_servizio(client: AsyncClient):
    indirizzo = await create_indirizzo(client)
    response = await client.post(
        "/api/v1/servizi/", json=servizio_payload(indirizzo["id"])
    )
    assert response.status_code == 201
    data = response.json()
    assert data["descrizione_servizio"] == "Processione Sant'Antonio"
    assert data["anno"] == 2026
    assert data["indirizzo_id"] == indirizzo["id"]


@pytest.mark.asyncio
async def test_create_servizio_indirizzo_not_found(client: AsyncClient):
    response = await client.post("/api/v1/servizi/", json=servizio_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_servizio_not_found(client: AsyncClient):
    response = await client.get("/api/v1/servizi/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_servizi_empty(client: AsyncClient):
    response = await client.get("/api/v1/servizi/")
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_list_servizi_filter_anno(client: AsyncClient):
    indirizzo = await create_indirizzo(client)
    await client.post(
        "/api/v1/servizi/", json=servizio_payload(indirizzo["id"], anno=2025)
    )
    await client.post(
        "/api/v1/servizi/", json=servizio_payload(indirizzo["id"], anno=2026)
    )
    response = await client.get("/api/v1/servizi/?anno=2026")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["anno"] == 2026


@pytest.mark.asyncio
async def test_update_servizio(client: AsyncClient):
    servizio = await create_servizio(client)
    response = await client.patch(
        f"/api/v1/servizi/{servizio['id']}", json={"note": "Annullato per pioggia"}
    )
    assert response.status_code == 200
    assert response.json()["note"] == "Annullato per pioggia"


@pytest.mark.asyncio
async def test_delete_servizio(client: AsyncClient):
    servizio = await create_servizio(client)
    response = await client.delete(f"/api/v1/servizi/{servizio['id']}")
    assert response.status_code == 204
    response = await client.get(f"/api/v1/servizi/{servizio['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_servizio_with_ricevuta_blocked(client: AsyncClient):
    servizio = await create_servizio(client)
    esterno = await create_esterno(client)
    await client.post(
        "/api/v1/ricevute/",
        json={
            "servizio_id": servizio["id"],
            "esterno_id": esterno["id"],
            "data_ricevuta": "2026-06-14T10:00:00",
            "importo": 100.0,
        },
    )
    response = await client.delete(f"/api/v1/servizi/{servizio['id']}")
    assert response.status_code == 409
