from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_indirizzo(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/indirizzi/",
        json={"tipo_indirizzo_codice": 4, "prima_riga": "Piazza Chiesa"},
    )
    return response.json()


def committente_payload(**overrides) -> dict:
    payload = {"denominazione": "Parrocchia San Giovanni"}
    payload.update(overrides)
    return payload


async def create_committente(client: AsyncClient, **overrides) -> dict:
    response = await client.post(
        "/api/v1/committenti/", json=committente_payload(**overrides)
    )
    return response.json()


@pytest.mark.asyncio
async def test_create_committente(client: AsyncClient):
    response = await client.post("/api/v1/committenti/", json=committente_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["denominazione"] == "Parrocchia San Giovanni"
    assert data["indirizzo_id"] is None


@pytest.mark.asyncio
async def test_create_committente_con_indirizzo(client: AsyncClient):
    indirizzo = await create_indirizzo(client)
    response = await client.post(
        "/api/v1/committenti/",
        json=committente_payload(indirizzo_id=indirizzo["id"]),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["indirizzo_id"] == indirizzo["id"]
    assert data["indirizzo"]["id"] == indirizzo["id"]


@pytest.mark.asyncio
async def test_create_committente_indirizzo_not_found(client: AsyncClient):
    response = await client.post(
        "/api/v1/committenti/", json=committente_payload(indirizzo_id=999)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_committente_not_found(client: AsyncClient):
    response = await client.get("/api/v1/committenti/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_committenti_empty(client: AsyncClient):
    response = await client.get("/api/v1/committenti/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_list_committenti(client: AsyncClient):
    await create_committente(client, denominazione="Comune di Cabras")
    await create_committente(client, denominazione="Pro Loco")
    response = await client.get("/api/v1/committenti/")
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2


@pytest.mark.asyncio
async def test_update_committente(client: AsyncClient):
    committente = await create_committente(client)
    response = await client.patch(
        f"/api/v1/committenti/{committente['id']}",
        json={"note": "Referente storico"},
    )
    assert response.status_code == 200
    assert response.json()["note"] == "Referente storico"


@pytest.mark.asyncio
async def test_update_committente_not_found(client: AsyncClient):
    response = await client.patch(
        "/api/v1/committenti/999", json={"denominazione": "X"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_committente(client: AsyncClient):
    committente = await create_committente(client)
    response = await client.delete(f"/api/v1/committenti/{committente['id']}")
    assert response.status_code == 204
    response = await client.get(f"/api/v1/committenti/{committente['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_committente_not_found(client: AsyncClient):
    response = await client.delete("/api/v1/committenti/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_committente_con_servizi_blocked(client: AsyncClient):
    indirizzo = await create_indirizzo(client)
    committente = await create_committente(client)
    await client.post(
        "/api/v1/servizi/",
        json={
            "banda_codice": 1,
            "anno": 2026,
            "descrizione_servizio": "Festa patronale",
            "data_servizio": "2026-06-13T18:00:00",
            "indirizzo_id": indirizzo["id"],
            "committente_id": committente["id"],
        },
    )
    response = await client.delete(f"/api/v1/committenti/{committente['id']}")
    assert response.status_code == 409
