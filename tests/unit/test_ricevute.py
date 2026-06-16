from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_servizio(client: AsyncClient) -> dict:
    indirizzo = await client.post(
        "/api/v1/indirizzi/",
        json={"tipo_indirizzo_codice": 4, "prima_riga": "Piazza Chiesa"},
    )
    response = await client.post(
        "/api/v1/servizi/",
        json={
            "banda_codice": 1,
            "anno": 2026,
            "descrizione_servizio": "Concerto estivo",
            "data_servizio": "2026-07-20T21:00:00",
            "indirizzo_id": indirizzo.json()["id"],
        },
    )
    return response.json()


async def create_esterno(client: AsyncClient, codice: str = "E001") -> dict:
    persona = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": "Gino", "cognome": "Esterni"},
    )
    response = await client.post(
        "/api/v1/esterni/",
        json={
            "persona_id": persona.json()["id"],
            "codice_esterno": codice,
            "strumento_codice": 5,
        },
    )
    return response.json()


def ricevuta_payload(servizio_id: int, esterno_id: int, **overrides) -> dict:
    payload = {
        "servizio_id": servizio_id,
        "esterno_id": esterno_id,
        "data_ricevuta": "2026-07-21T10:00:00",
        "importo": 150.50,
        "note_in_stampa": "Compenso servizio",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_ricevuta(client: AsyncClient):
    servizio = await create_servizio(client)
    esterno = await create_esterno(client)
    response = await client.post(
        "/api/v1/ricevute/", json=ricevuta_payload(servizio["id"], esterno["id"])
    )
    assert response.status_code == 201
    data = response.json()
    assert data["servizio_id"] == servizio["id"]
    assert data["esterno_id"] == esterno["id"]
    assert data["importo"] == 150.50


@pytest.mark.asyncio
async def test_create_ricevuta_servizio_not_found(client: AsyncClient):
    esterno = await create_esterno(client)
    response = await client.post(
        "/api/v1/ricevute/", json=ricevuta_payload(999, esterno["id"])
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_ricevuta_esterno_not_found(client: AsyncClient):
    servizio = await create_servizio(client)
    response = await client.post(
        "/api/v1/ricevute/", json=ricevuta_payload(servizio["id"], 999)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_ricevuta_not_found(client: AsyncClient):
    response = await client.get("/api/v1/ricevute/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_ricevute_servizio(client: AsyncClient):
    servizio = await create_servizio(client)
    esterno1 = await create_esterno(client, "E001")
    esterno2 = await create_esterno(client, "E002")
    await client.post(
        "/api/v1/ricevute/", json=ricevuta_payload(servizio["id"], esterno1["id"])
    )
    await client.post(
        "/api/v1/ricevute/", json=ricevuta_payload(servizio["id"], esterno2["id"])
    )
    response = await client.get(f"/api/v1/ricevute/servizio/{servizio['id']}")
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2


@pytest.mark.asyncio
async def test_get_ricevute_servizio_not_found(client: AsyncClient):
    response = await client.get("/api/v1/ricevute/servizio/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_ricevuta(client: AsyncClient):
    servizio = await create_servizio(client)
    esterno = await create_esterno(client)
    created = await client.post(
        "/api/v1/ricevute/", json=ricevuta_payload(servizio["id"], esterno["id"])
    )
    ricevuta_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/ricevute/{ricevuta_id}", json={"importo": 200.0}
    )
    assert response.status_code == 200
    assert response.json()["importo"] == 200.0


@pytest.mark.asyncio
async def test_delete_ricevuta(client: AsyncClient):
    servizio = await create_servizio(client)
    esterno = await create_esterno(client)
    created = await client.post(
        "/api/v1/ricevute/", json=ricevuta_payload(servizio["id"], esterno["id"])
    )
    ricevuta_id = created.json()["id"]
    response = await client.delete(f"/api/v1/ricevute/{ricevuta_id}")
    assert response.status_code == 204
    response = await client.get(f"/api/v1/ricevute/{ricevuta_id}")
    assert response.status_code == 404
