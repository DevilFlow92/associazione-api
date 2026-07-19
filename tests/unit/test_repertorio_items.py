from __future__ import annotations

import pytest
from httpx import AsyncClient


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
        "descrizione_servizio": "Concerto in piazza",
        "data_servizio": "2026-06-13T18:00:00",
        "indirizzo_id": indirizzo["id"],
    }
    payload.update(overrides)
    response = await client.post("/api/v1/servizi/", json=payload)
    return response.json()


async def create_nome_parte(client: AsyncClient, **overrides) -> dict:
    payload = {"nome": "Marcia Trionfale", "tipo_spartito_codice": 1, "banda_codice": 1}
    payload.update(overrides)
    response = await client.post("/api/v1/nome-parti/", json=payload)
    return response.json()


def repertorio_item_payload(nome_parte_id: int, servizio_id: int, **overrides) -> dict:
    payload = {"nome_parte_id": nome_parte_id, "servizio_id": servizio_id, "ordine": 1}
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_repertorio_item(client: AsyncClient):
    nome_parte = await create_nome_parte(client)
    servizio = await create_servizio(client)
    response = await client.post(
        "/api/v1/repertorio/",
        json=repertorio_item_payload(nome_parte["id"], servizio["id"]),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nome_parte_id"] == nome_parte["id"]
    assert data["servizio_id"] == servizio["id"]
    assert data["ordine"] == 1
    assert data["nome_parte"] is not None
    assert data["nome_parte"]["nome"] == "Marcia Trionfale"


@pytest.mark.asyncio
async def test_create_repertorio_item_nome_parte_not_found(client: AsyncClient):
    servizio = await create_servizio(client)
    response = await client.post(
        "/api/v1/repertorio/", json=repertorio_item_payload(999, servizio["id"])
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_repertorio_item_servizio_not_found(client: AsyncClient):
    nome_parte = await create_nome_parte(client)
    response = await client.post(
        "/api/v1/repertorio/", json=repertorio_item_payload(nome_parte["id"], 999)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_repertorio_item_duplicato(client: AsyncClient):
    """La stessa NomeParte non può comparire due volte nel programma dello
    stesso servizio."""
    nome_parte = await create_nome_parte(client)
    servizio = await create_servizio(client)
    await client.post(
        "/api/v1/repertorio/",
        json=repertorio_item_payload(nome_parte["id"], servizio["id"]),
    )
    response = await client.post(
        "/api/v1/repertorio/",
        json=repertorio_item_payload(nome_parte["id"], servizio["id"], ordine=2),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_repertorio_item(client: AsyncClient):
    nome_parte = await create_nome_parte(client)
    servizio = await create_servizio(client)
    created = await client.post(
        "/api/v1/repertorio/",
        json=repertorio_item_payload(nome_parte["id"], servizio["id"]),
    )
    item_id = created.json()["id"]

    response = await client.delete(f"/api/v1/repertorio/{item_id}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/repertorio/{item_id}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_repertorio_item_not_found(client: AsyncClient):
    response = await client.delete("/api/v1/repertorio/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_repertorio_servizio_ordinato(client: AsyncClient):
    servizio = await create_servizio(client)
    nome_parte1 = await create_nome_parte(client, nome="Marcia Trionfale")
    nome_parte2 = await create_nome_parte(client, nome="Inno alla Gioia")
    await client.post(
        "/api/v1/repertorio/",
        json=repertorio_item_payload(nome_parte1["id"], servizio["id"], ordine=2),
    )
    await client.post(
        "/api/v1/repertorio/",
        json=repertorio_item_payload(nome_parte2["id"], servizio["id"], ordine=1),
    )

    response = await client.get(f"/api/v1/repertorio/servizio/{servizio['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 2
    nomi = [item["nome_parte"]["nome"] for item in data["items"]]
    assert nomi == ["Inno alla Gioia", "Marcia Trionfale"]


@pytest.mark.asyncio
async def test_get_repertorio_servizio_not_found(client: AsyncClient):
    response = await client.get("/api/v1/repertorio/servizio/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_repertorio_item_ordine(client: AsyncClient):
    nome_parte = await create_nome_parte(client)
    servizio = await create_servizio(client)
    created = await client.post(
        "/api/v1/repertorio/",
        json=repertorio_item_payload(nome_parte["id"], servizio["id"]),
    )
    item_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/repertorio/{item_id}",
        json={"ordine": 5, "note": "Bis finale"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ordine"] == 5
    assert data["note"] == "Bis finale"
    assert data["nome_parte"] is not None
    assert data["nome_parte"]["nome"] == "Marcia Trionfale"


@pytest.mark.asyncio
async def test_update_repertorio_item_not_found(client: AsyncClient):
    response = await client.patch("/api/v1/repertorio/999", json={"ordine": 2})
    assert response.status_code == 404
