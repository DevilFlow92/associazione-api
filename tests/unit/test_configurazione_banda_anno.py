from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.models.lookups import SezioneRendiconto
from app.models.utente import TipoUtente, Utente

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


# ── Seed tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_first_configurazione_seeds_voci(client: AsyncClient):
    """Creating the first configurazione for a banda auto-seeds 4 voci."""
    await create_cfg(client, banda_codice=1, anno=2024)
    response = await client.get("/api/v1/voci-contabilita/?banda_codice=1")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 4
    names = {v["voce_contabilita"] for v in data["items"]}
    assert names == {
        "Quote associative",
        "Saldo iniziale",
        "Versamento in banca",
        "Spese bancarie",
    }
    # Verify rendiconto classification of "Quote associative"
    quote = next(
        v for v in data["items"] if v["voce_contabilita"] == "Quote associative"
    )
    assert quote["sezione_rendiconto_codice"] == 2  # Entrate
    assert quote["voce_rendiconto_codice"] == 2  # A) Entrate da attività …
    assert quote["sottovoce_rendiconto_codice"] == 6  # 1) Entrate da quote …


@pytest.mark.asyncio
async def test_create_second_configurazione_does_not_reseed(client: AsyncClient):
    """A second configurazione for the same banda does not duplicate the voci."""
    await create_cfg(client, banda_codice=1, anno=2024)
    await create_cfg(client, banda_codice=1, anno=2025)
    response = await client.get("/api/v1/voci-contabilita/?banda_codice=1")
    assert response.status_code == 200
    # Still exactly 4 voci — no duplicates from the second create.
    assert response.json()["meta"]["total_items"] == 4


# ── Chiudi / Riapri tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chiudi_anno_sets_fields(client: AsyncClient):
    cfg = await create_cfg(client)
    response = await client.post(f"{BASE}/{cfg['id']}/chiudi")
    assert response.status_code == 200
    data = response.json()
    assert data["chiuso"] is True
    assert data["data_chiusura"] is not None
    assert data["chiuso_da_utente_id"] is not None


@pytest.mark.asyncio
async def test_chiudi_anno_already_closed_409(client: AsyncClient):
    cfg = await create_cfg(client)
    await client.post(f"{BASE}/{cfg['id']}/chiudi")
    response = await client.post(f"{BASE}/{cfg['id']}/chiudi")
    assert response.status_code == 409
    assert "chiuso" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_riapri_anno_superuser_ok(client: AsyncClient):
    cfg = await create_cfg(client)
    await client.post(f"{BASE}/{cfg['id']}/chiudi")
    response = await client.post(f"{BASE}/{cfg['id']}/riapri")
    assert response.status_code == 200
    data = response.json()
    assert data["chiuso"] is False
    assert data["data_chiusura"] is None
    assert data["chiuso_da_utente_id"] is None


@pytest.mark.asyncio
async def test_riapri_anno_non_superuser_forbidden(client: AsyncClient):
    from main import app

    cfg = await create_cfg(client)
    await client.post(f"{BASE}/{cfg['id']}/chiudi")

    saved = dict(app.dependency_overrides)

    async def non_super():
        return Utente(
            id=99, tipo=TipoUtente.UMANO, email="user@example.com", superuser=False
        )

    app.dependency_overrides[get_current_user] = non_super
    try:
        response = await client.post(f"{BASE}/{cfg['id']}/riapri")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_riapri_anno_already_open_409(client: AsyncClient):
    cfg = await create_cfg(client)
    response = await client.post(f"{BASE}/{cfg['id']}/riapri")
    assert response.status_code == 409
    assert "aperto" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_seed_missing_lookup_descrizione_raises(
    client: AsyncClient, db_session: AsyncSession
):
    """If a required sezione lookup is missing, create returns 422 and no
    partial state (no voci and no configurazione) is left in the DB."""
    # Remove the "Entrate" sezione so the lookup for "Quote associative" fails.
    await db_session.execute(
        delete(SezioneRendiconto).where(SezioneRendiconto.codice == 2)
    )
    await db_session.commit()

    response = await client.post(f"{BASE}/", json=cfg_payload())
    assert response.status_code == 422
    assert "Entrate" in response.json()["detail"]

    # No voci should have been inserted (transaction rolled back).
    voci_response = await client.get("/api/v1/voci-contabilita/?banda_codice=1")
    assert voci_response.json()["meta"]["total_items"] == 0

    # No configurazione should have been inserted either.
    cfg_response = await client.get(f"{BASE}/?banda_codice=1")
    assert cfg_response.json()["meta"]["total_items"] == 0
