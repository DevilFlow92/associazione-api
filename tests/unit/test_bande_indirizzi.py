from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_banda(client: AsyncClient, codice: int = 1) -> dict:
    response = await client.post(
        "/api/v1/bande/", json={"codice": codice, "descrizione": "Banda Test"}
    )
    return response.json()


async def create_indirizzo(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/indirizzi/",
        json={"tipo_indirizzo_codice": 1, "prima_riga": "Sede Legale 1"},
    )
    return response.json()


@pytest.mark.asyncio
async def test_banda_indirizzi_link_unlink(client: AsyncClient):
    banda = await create_banda(client)
    indirizzo = await create_indirizzo(client)

    response = await client.put(
        f"/api/v1/bande/{banda['codice']}/indirizzi/{indirizzo['id']}"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == indirizzo["id"]

    # idempotent re-link
    response = await client.put(
        f"/api/v1/bande/{banda['codice']}/indirizzi/{indirizzo['id']}"
    )
    assert len(response.json()) == 1

    response = await client.get(f"/api/v1/bande/{banda['codice']}/indirizzi")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = await client.delete(
        f"/api/v1/bande/{banda['codice']}/indirizzi/{indirizzo['id']}"
    )
    assert response.status_code == 204

    response = await client.get(f"/api/v1/bande/{banda['codice']}/indirizzi")
    assert response.json() == []


@pytest.mark.asyncio
async def test_link_indirizzo_banda_not_found(client: AsyncClient):
    indirizzo = await create_indirizzo(client)
    response = await client.put(f"/api/v1/bande/999/indirizzi/{indirizzo['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_link_indirizzo_not_found(client: AsyncClient):
    banda = await create_banda(client)
    response = await client.put(f"/api/v1/bande/{banda['codice']}/indirizzi/999")
    assert response.status_code == 404
