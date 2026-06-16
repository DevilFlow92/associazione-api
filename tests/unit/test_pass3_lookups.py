from __future__ import annotations

import pytest
from httpx import AsyncClient

# ── TipoDocumento ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_tipo_documento(client: AsyncClient):
    response = await client.post(
        "/api/v1/tipi-documento/",
        json={"codice": 1, "descrizione": "Modulo iscrizione"},
    )
    assert response.status_code == 201
    assert response.json() == {"codice": 1, "descrizione": "Modulo iscrizione"}
    response = await client.get("/api/v1/tipi-documento/1")
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Modulo iscrizione"


@pytest.mark.asyncio
async def test_tipo_documento_duplicate(client: AsyncClient):
    await client.post(
        "/api/v1/tipi-documento/", json={"codice": 1, "descrizione": "Ricevuta"}
    )
    response = await client.post(
        "/api/v1/tipi-documento/", json={"codice": 1, "descrizione": "Altro"}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_tipo_documento_not_found(client: AsyncClient):
    assert (await client.get("/api/v1/tipi-documento/999")).status_code == 404


@pytest.mark.asyncio
async def test_update_tipo_documento(client: AsyncClient):
    await client.post(
        "/api/v1/tipi-documento/", json={"codice": 3, "descrizione": "Spartito"}
    )
    response = await client.patch(
        "/api/v1/tipi-documento/3", json={"descrizione": "Partitura"}
    )
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Partitura"


@pytest.mark.asyncio
async def test_delete_tipo_documento(client: AsyncClient):
    await client.post(
        "/api/v1/tipi-documento/", json={"codice": 6, "descrizione": "Altro"}
    )
    assert (await client.delete("/api/v1/tipi-documento/6")).status_code == 204
    assert (await client.get("/api/v1/tipi-documento/6")).status_code == 404


# ── TipoSpartito ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_tipo_spartito(client: AsyncClient):
    response = await client.post(
        "/api/v1/tipi-spartito/", json={"codice": 1, "descrizione": "Marcia festiva"}
    )
    assert response.status_code == 201
    assert response.json()["descrizione"] == "Marcia festiva"


@pytest.mark.asyncio
async def test_tipo_spartito_not_found(client: AsyncClient):
    assert (await client.get("/api/v1/tipi-spartito/999")).status_code == 404


@pytest.mark.asyncio
async def test_delete_tipo_spartito(client: AsyncClient):
    await client.post(
        "/api/v1/tipi-spartito/", json={"codice": 4, "descrizione": "Brano da concerto"}
    )
    assert (await client.delete("/api/v1/tipi-spartito/4")).status_code == 204


# ── StatoIscrizione ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_stato_iscrizione(client: AsyncClient):
    response = await client.post(
        "/api/v1/stati-iscrizione/", json={"codice": 2, "descrizione": "Pagata"}
    )
    assert response.status_code == 201
    assert response.json()["descrizione"] == "Pagata"


@pytest.mark.asyncio
async def test_stato_iscrizione_not_found(client: AsyncClient):
    assert (await client.get("/api/v1/stati-iscrizione/999")).status_code == 404


@pytest.mark.asyncio
async def test_update_stato_iscrizione(client: AsyncClient):
    await client.post(
        "/api/v1/stati-iscrizione/", json={"codice": 3, "descrizione": "Annullata"}
    )
    response = await client.patch(
        "/api/v1/stati-iscrizione/3", json={"descrizione": "Revocata"}
    )
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Revocata"
