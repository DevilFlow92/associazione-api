from __future__ import annotations

import pytest
from httpx import AsyncClient


def voce_payload(**overrides) -> dict:
    payload = {
        "banda_codice": 1,
        "voce_contabilita": "Cancelleria",
        "sezione_rendiconto_codice": 1,
        "voce_rendiconto_codice": 1,
        "sottovoce_rendiconto_codice": 2,
    }
    payload.update(overrides)
    return payload


async def create_voce(client: AsyncClient, **overrides) -> dict:
    response = await client.post(
        "/api/v1/voci-contabilita/", json=voce_payload(**overrides)
    )
    return response.json()


@pytest.mark.asyncio
async def test_create_voce_contabilita(client: AsyncClient):
    response = await client.post("/api/v1/voci-contabilita/", json=voce_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["voce_contabilita"] == "Cancelleria"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_voce_contabilita_not_found(client: AsyncClient):
    response = await client.get("/api/v1/voci-contabilita/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_voci_contabilita_filter_banda(client: AsyncClient):
    await create_voce(client, banda_codice=1)
    await create_voce(client, banda_codice=2)
    response = await client.get("/api/v1/voci-contabilita/?banda_codice=2")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["banda_codice"] == 2


@pytest.mark.asyncio
async def test_update_voce_contabilita(client: AsyncClient):
    voce = await create_voce(client)
    response = await client.patch(
        f"/api/v1/voci-contabilita/{voce['id']}",
        json={"voce_contabilita": "Spese postali"},
    )
    assert response.status_code == 200
    assert response.json()["voce_contabilita"] == "Spese postali"


@pytest.mark.asyncio
async def test_delete_voce_contabilita(client: AsyncClient):
    voce = await create_voce(client)
    response = await client.delete(f"/api/v1/voci-contabilita/{voce['id']}")
    assert response.status_code == 204
    response = await client.get(f"/api/v1/voci-contabilita/{voce['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_voce_contabilita_with_flusso_blocked(client: AsyncClient):
    voce = await create_voce(client)
    await client.post(
        "/api/v1/flussi-cassa/",
        json={
            "data_registrazione": "2026-01-15T00:00:00",
            "descrizione_operazione": "Acquisto cancelleria",
            "voce_contabilita_id": voce["id"],
            "importo": 45.00,
            "segno": "-",
            "natura_flusso_codice": 1,
        },
    )
    response = await client.delete(f"/api/v1/voci-contabilita/{voce['id']}")
    assert response.status_code == 409
