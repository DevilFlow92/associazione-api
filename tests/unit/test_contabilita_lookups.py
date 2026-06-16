from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_natura_flusso_crud(client: AsyncClient):
    response = await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Cassa"}
    )
    assert response.status_code == 201

    response = await client.patch(
        "/api/v1/nature-flusso/1", json={"descrizione": "Banca"}
    )
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Banca"


@pytest.mark.asyncio
async def test_natura_flusso_duplicate_codice(client: AsyncClient):
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Cassa"}
    )
    response = await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Banca"}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_sezione_rendiconto_not_found(client: AsyncClient):
    response = await client.get("/api/v1/sezioni-rendiconto/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_voce_rendiconto_create(client: AsyncClient):
    descrizione = "A) Uscite da attività di interesse generale"
    response = await client.post(
        "/api/v1/voci-rendiconto/", json={"codice": 1, "descrizione": descrizione}
    )
    assert response.status_code == 201
    assert response.json()["descrizione"] == descrizione


@pytest.mark.asyncio
async def test_sottovoce_rendiconto_create(client: AsyncClient):
    response = await client.post(
        "/api/v1/sottovoci-rendiconto/",
        json={"codice": 1, "descrizione": "1) Materie prime, di consumo e di merci"},
    )
    assert response.status_code == 201
