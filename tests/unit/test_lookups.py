from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_strumento(client: AsyncClient):
    response = await client.post(
        "/api/v1/strumenti/", json={"codice": 1, "descrizione": "Flauto"}
    )
    assert response.status_code == 201
    assert response.json() == {"codice": 1, "descrizione": "Flauto"}

    response = await client.get("/api/v1/strumenti/1")
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Flauto"


@pytest.mark.asyncio
async def test_create_strumento_duplicate_codice(client: AsyncClient):
    await client.post("/api/v1/strumenti/", json={"codice": 1, "descrizione": "Flauto"})
    response = await client.post(
        "/api/v1/strumenti/", json={"codice": 1, "descrizione": "Ottavino"}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_strumento_not_found(client: AsyncClient):
    response = await client.get("/api/v1/strumenti/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_strumento(client: AsyncClient):
    await client.post("/api/v1/strumenti/", json={"codice": 1, "descrizione": "Flauto"})
    response = await client.patch(
        "/api/v1/strumenti/1", json={"descrizione": "Ottavino"}
    )
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Ottavino"


@pytest.mark.asyncio
async def test_update_strumento_not_found(client: AsyncClient):
    response = await client.patch("/api/v1/strumenti/999", json={"descrizione": "X"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_strumento(client: AsyncClient):
    await client.post("/api/v1/strumenti/", json={"codice": 1, "descrizione": "Flauto"})
    response = await client.delete("/api/v1/strumenti/1")
    assert response.status_code == 204

    response = await client.get("/api/v1/strumenti/1")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_strumenti_paginated(client: AsyncClient):
    for codice in range(1, 4):
        await client.post(
            "/api/v1/strumenti/",
            json={"codice": codice, "descrizione": f"Strumento {codice}"},
        )
    response = await client.get("/api/v1/strumenti/?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["meta"]["total_items"] == 3
    assert data["meta"]["total_pages"] == 2
    assert data["meta"]["has_next"] is True


@pytest.mark.asyncio
async def test_regione_carries_foreign_key(client: AsyncClient):
    response = await client.post(
        "/api/v1/regioni/",
        json={"codice": 1, "descrizione": "Sardegna", "stato_codice": 1},
    )
    assert response.status_code == 201
    assert response.json()["stato_codice"] == 1


@pytest.mark.asyncio
async def test_comune_carries_extra_fields(client: AsyncClient):
    response = await client.post(
        "/api/v1/comuni/",
        json={
            "codice": 5535,
            "descrizione": "Quartu Sant'Elena",
            "codice_catastale": "B354",
            "provincia_codice": 92,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["codice_catastale"] == "B354"
    assert data["provincia_codice"] == 92
