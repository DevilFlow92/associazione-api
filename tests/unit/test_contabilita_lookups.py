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
    descrizione = "Voce di prova"
    response = await client.post(
        "/api/v1/voci-rendiconto/",
        json={"codice": 90, "descrizione": descrizione, "sezione_codice": 1},
    )
    assert response.status_code == 201
    assert response.json()["descrizione"] == descrizione
    assert response.json()["sezione_codice"] == 1


@pytest.mark.asyncio
async def test_sottovoce_rendiconto_create(client: AsyncClient):
    response = await client.post(
        "/api/v1/sottovoci-rendiconto/",
        json={"codice": 90, "descrizione": "Sottovoce di prova"},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_voci_rendiconto_filter_sezione(client: AsyncClient):
    response = await client.get(
        "/api/v1/voci-rendiconto/?sezione_codice=2&page_size=100"
    )
    assert response.status_code == 200
    data = response.json()
    # Solo le voci "Entrate" (sezione 2).
    assert {item["codice"] for item in data["items"]} == {2, 4, 6, 9, 11, 13}
    assert all(item["sezione_codice"] == 2 for item in data["items"])


@pytest.mark.asyncio
async def test_sottovoci_rendiconto_filter_voce_uscite_generiche(client: AsyncClient):
    response = await client.get(
        "/api/v1/sottovoci-rendiconto/?voce_codice=1&page_size=100"
    )
    assert response.status_code == 200
    data = response.json()
    # Le 5 sottovoci generiche di uscita sotto A) Uscite (voce 1).
    assert {item["codice"] for item in data["items"]} == {1, 2, 3, 4, 5}


@pytest.mark.asyncio
async def test_sottovoci_rendiconto_filter_voce_n_to_m(client: AsyncClient):
    """Le stesse 5 sottovoci generiche di uscita sono condivise da B) Uscite
    (voce 3): è la prova del legame N:M voce↔sottovoce."""
    response = await client.get(
        "/api/v1/sottovoci-rendiconto/?voce_codice=3&page_size=100"
    )
    assert response.status_code == 200
    data = response.json()
    assert {item["codice"] for item in data["items"]} == {1, 2, 3, 4, 5}


@pytest.mark.asyncio
async def test_sottovoci_rendiconto_filter_voce_entrate(client: AsyncClient):
    response = await client.get(
        "/api/v1/sottovoci-rendiconto/?voce_codice=2&page_size=100"
    )
    assert response.status_code == 200
    data = response.json()
    # Le 10 sottovoci entrate specifiche di A) Entrate (voce 2).
    codici = {item["codice"] for item in data["items"]}
    assert codici == {6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
    assert data["meta"]["total_items"] == 10
