from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_socio(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/soci/",
        json={
            "nome": "Mario",
            "cognome": "Rossi",
            "email": "mario.rossi@test.com",
            "strumento": "Tromba",
        },
    )
    return response.json()


@pytest.mark.asyncio
async def test_create_iscrizione(client: AsyncClient):
    socio = await create_socio(client)
    response = await client.post(
        "/api/v1/iscrizioni/",
        json={
            "socio_id": socio["id"],
            "anno": 2026,
            "quota_dovuta": 50.0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["socio_id"] == socio["id"]
    assert data["anno"] == 2026
    assert data["stato_pagamento"] == "non_pagato"


@pytest.mark.asyncio
async def test_create_iscrizione_duplicata(client: AsyncClient):
    socio = await create_socio(client)
    payload = {"socio_id": socio["id"], "anno": 2026, "quota_dovuta": 50.0}
    await client.post("/api/v1/iscrizioni/", json=payload)
    response = await client.post("/api/v1/iscrizioni/", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_iscrizione_socio_inesistente(client: AsyncClient):
    response = await client.post(
        "/api/v1/iscrizioni/",
        json={"socio_id": 999, "anno": 2026, "quota_dovuta": 50.0},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_iscrizione(client: AsyncClient):
    socio = await create_socio(client)
    iscrizione = await client.post(
        "/api/v1/iscrizioni/",
        json={"socio_id": socio["id"], "anno": 2026, "quota_dovuta": 50.0},
    )
    iscrizione_id = iscrizione.json()["id"]
    response = await client.patch(
        f"/api/v1/iscrizioni/{iscrizione_id}",
        json={"quota_pagata": 50.0, "stato_pagamento": "pagato"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stato_pagamento"] == "pagato"
    assert data["quota_pagata"] == 50.0
