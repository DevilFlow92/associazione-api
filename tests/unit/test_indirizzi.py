from __future__ import annotations

import pytest
from httpx import AsyncClient


def indirizzo_payload(**overrides) -> dict:
    payload = {
        "tipo_indirizzo_codice": 2,
        "prima_riga": "Via Merello 126",
        "cap": "09045",
        "numero_civico": "126",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_indirizzo(client: AsyncClient):
    response = await client.post("/api/v1/indirizzi/", json=indirizzo_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["prima_riga"] == "Via Merello 126"
    assert data["cap"] == "09045"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_indirizzo_not_found(client: AsyncClient):
    response = await client.get("/api/v1/indirizzi/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_indirizzi_empty(client: AsyncClient):
    response = await client.get("/api/v1/indirizzi/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_update_indirizzo(client: AsyncClient):
    created = await client.post("/api/v1/indirizzi/", json=indirizzo_payload())
    indirizzo_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/indirizzi/{indirizzo_id}", json={"interno": "Piano 1"}
    )
    assert response.status_code == 200
    assert response.json()["interno"] == "Piano 1"


@pytest.mark.asyncio
async def test_delete_indirizzo(client: AsyncClient):
    created = await client.post("/api/v1/indirizzi/", json=indirizzo_payload())
    indirizzo_id = created.json()["id"]
    response = await client.delete(f"/api/v1/indirizzi/{indirizzo_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/indirizzi/{indirizzo_id}")
    assert response.status_code == 404
