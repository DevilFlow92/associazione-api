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
        json={"tipo_indirizzo_codice": 2, "prima_riga": "Via Roma 1", "cap": "09045"},
    )
    return response.json()


@pytest.mark.asyncio
async def test_create_persona(client: AsyncClient):
    response = await client.post(
        "/api/v1/persone/",
        json={
            "banda_codice": 1,
            "nome": "Mario",
            "cognome": "Rossi",
            "codice_fiscale": "RSSMRA80A01H501U",
            "data_nascita": "1980-01-01",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Mario"
    assert data["data_nascita"] == "1980-01-01"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_persona_not_found(client: AsyncClient):
    response = await client.get("/api/v1/persone/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_persone_empty(client: AsyncClient):
    response = await client.get("/api/v1/persone/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_update_persona(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.patch(
        f"/api/v1/persone/{persona['id']}", json={"cognome": "Bianchi"}
    )
    assert response.status_code == 200
    assert response.json()["cognome"] == "Bianchi"
    assert response.json()["nome"] == "Mario"


@pytest.mark.asyncio
async def test_delete_persona(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.delete(f"/api/v1/persone/{persona['id']}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/persone/{persona['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_persona_with_socio_blocked(client: AsyncClient):
    persona = await create_persona(client)
    await client.post(
        "/api/v1/soci/",
        json={
            "persona_id": persona["id"],
            "codice_socio": "S001",
            "banda_codice": 1,
            "ruolo_banda_codice": 10,
        },
    )
    response = await client.delete(f"/api/v1/persone/{persona['id']}")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_persona_indirizzi_link_unlink(client: AsyncClient):
    persona = await create_persona(client)
    indirizzo = await create_indirizzo(client)

    # link
    response = await client.put(
        f"/api/v1/persone/{persona['id']}/indirizzi/{indirizzo['id']}"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == indirizzo["id"]

    # idempotent re-link
    response = await client.put(
        f"/api/v1/persone/{persona['id']}/indirizzi/{indirizzo['id']}"
    )
    assert len(response.json()) == 1

    # list
    response = await client.get(f"/api/v1/persone/{persona['id']}/indirizzi")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # unlink
    response = await client.delete(
        f"/api/v1/persone/{persona['id']}/indirizzi/{indirizzo['id']}"
    )
    assert response.status_code == 204

    response = await client.get(f"/api/v1/persone/{persona['id']}/indirizzi")
    assert response.json() == []


@pytest.mark.asyncio
async def test_link_indirizzo_persona_not_found(client: AsyncClient):
    indirizzo = await create_indirizzo(client)
    response = await client.put(f"/api/v1/persone/999/indirizzi/{indirizzo['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_link_indirizzo_not_found(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.put(f"/api/v1/persone/{persona['id']}/indirizzi/999")
    assert response.status_code == 404
