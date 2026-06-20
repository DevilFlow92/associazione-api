from __future__ import annotations

import pytest
from httpx import AsyncClient

BASE = "/api/v1/configurazione-banda-anno"


def cfg_payload(**overrides) -> dict:
    payload = {
        "banda_codice": 1,
        "anno": 2024,
        "quota_annuale_attesa": "100.00",
        "saldo_iniziale_cassa": "500.00",
        "saldo_iniziale_banca": "1000.00",
    }
    payload.update(overrides)
    return payload


async def create_cfg(client: AsyncClient, **overrides) -> dict:
    response = await client.post(f"{BASE}/", json=cfg_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_create(client: AsyncClient):
    response = await client.post(f"{BASE}/", json=cfg_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["banda_codice"] == 1
    assert data["anno"] == 2024
    assert "id" in data
    assert data["voce_contabilita_quote"] is None
    assert data["chiuso_da_utente"] is None


@pytest.mark.asyncio
async def test_create_duplicate_409(client: AsyncClient):
    await create_cfg(client)
    response = await client.post(f"{BASE}/", json=cfg_payload())
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_by_id(client: AsyncClient):
    cfg = await create_cfg(client)
    response = await client.get(f"{BASE}/{cfg['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == cfg["id"]


@pytest.mark.asyncio
async def test_get_by_id_not_found(client: AsyncClient):
    response = await client.get(f"{BASE}/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_by_banda_anno(client: AsyncClient):
    cfg = await create_cfg(client, banda_codice=1, anno=2025)
    response = await client.get(f"{BASE}/banda/1/anno/2025")
    assert response.status_code == 200
    assert response.json()["id"] == cfg["id"]


@pytest.mark.asyncio
async def test_get_by_banda_anno_not_found(client: AsyncClient):
    response = await client.get(f"{BASE}/banda/1/anno/1900")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update(client: AsyncClient):
    cfg = await create_cfg(client)
    response = await client.patch(
        f"{BASE}/{cfg['id']}",
        json={"quota_annuale_attesa": "200.00"},
    )
    assert response.status_code == 200
    assert float(response.json()["quota_annuale_attesa"]) == 200.00


@pytest.mark.asyncio
async def test_update_chiuso_blocks_409(client: AsyncClient):
    cfg = await create_cfg(client)
    # close the record
    await client.patch(f"{BASE}/{cfg['id']}", json={"chiuso": True})
    # attempt update on closed record
    response = await client.patch(
        f"{BASE}/{cfg['id']}",
        json={"quota_annuale_attesa": "300.00"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete(client: AsyncClient):
    cfg = await create_cfg(client)
    response = await client.delete(f"{BASE}/{cfg['id']}")
    assert response.status_code == 204
    assert (await client.get(f"{BASE}/{cfg['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_chiuso_blocks_409(client: AsyncClient):
    cfg = await create_cfg(client)
    await client.patch(f"{BASE}/{cfg['id']}", json={"chiuso": True})
    response = await client.delete(f"{BASE}/{cfg['id']}")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_filter_by_banda(client: AsyncClient):
    await create_cfg(client, banda_codice=1, anno=2024)
    await create_cfg(client, banda_codice=2, anno=2024)
    response = await client.get(f"{BASE}/?banda_codice=2")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["banda_codice"] == 2
