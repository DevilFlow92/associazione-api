from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_socio(client: AsyncClient):
    response = await client.post(
        "/api/v1/soci/",
        json={
            "nome": "Mario",
            "cognome": "Rossi",
            "email": "mario.rossi@test.com",
            "strumento": "Tromba",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "mario.rossi@test.com"
    assert data["stato"] == "attivo"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_socio_duplicate_email(client: AsyncClient):
    payload = {
        "nome": "Mario",
        "cognome": "Rossi",
        "email": "mario.rossi@test.com",
        "strumento": "Tromba",
    }
    await client.post("/api/v1/soci/", json=payload)
    response = await client.post("/api/v1/soci/", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_socio_not_found(client: AsyncClient):
    response = await client.get("/api/v1/soci/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_soci_empty(client: AsyncClient):
    response = await client.get("/api/v1/soci/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0
    assert data["meta"]["page"] == 1
