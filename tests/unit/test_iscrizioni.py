from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_socio(client: AsyncClient, codice: str = "S001") -> dict:
    persona = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": "Mario", "cognome": "Rossi"},
    )
    response = await client.post(
        "/api/v1/soci/",
        json={
            "persona_id": persona.json()["id"],
            "codice_socio": codice,
            "banda_codice": 1,
            "ruolo_banda_codice": 10,
        },
    )
    assert response.status_code == 201
    return response.json()


def iscrizione_payload(socio_id: int, **overrides) -> dict:
    payload = {
        "socio_id": socio_id,
        "anno": 2026,
        "quota_partecipazione": 80.0,
        "stato_iscrizione_codice": 1,
        "data_iscrizione": "2026-01-10",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_iscrizione(client: AsyncClient):
    socio = await create_socio(client)
    response = await client.post(
        "/api/v1/iscrizioni/", json=iscrizione_payload(socio["id"])
    )
    assert response.status_code == 201
    data = response.json()
    assert data["socio_id"] == socio["id"]
    assert data["anno"] == 2026
    assert data["quota_partecipazione"] == 80.0
    assert data["stato_iscrizione_codice"] == 1
    assert data["ricevuta_id"] is None
    assert data["documento_id"] is None


@pytest.mark.asyncio
async def test_create_iscrizione_socio_not_found(client: AsyncClient):
    response = await client.post("/api/v1/iscrizioni/", json=iscrizione_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_iscrizione_duplicata(client: AsyncClient):
    """Un socio non può iscriversi due volte nello stesso anno."""
    socio = await create_socio(client)
    await client.post("/api/v1/iscrizioni/", json=iscrizione_payload(socio["id"]))
    response = await client.post(
        "/api/v1/iscrizioni/", json=iscrizione_payload(socio["id"])
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_iscrizione_not_found(client: AsyncClient):
    response = await client.get("/api/v1/iscrizioni/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_iscrizioni_empty(client: AsyncClient):
    response = await client.get("/api/v1/iscrizioni/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_list_iscrizioni_filtro_socio(client: AsyncClient):
    socio1 = await create_socio(client, "S001")
    socio2 = await create_socio(client, "S002")
    await client.post("/api/v1/iscrizioni/", json=iscrizione_payload(socio1["id"]))
    await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio2["id"], anno=2025),
    )
    response = await client.get(f"/api/v1/iscrizioni/?socio_id={socio1['id']}")
    assert response.json()["meta"]["total_items"] == 1


@pytest.mark.asyncio
async def test_update_iscrizione(client: AsyncClient):
    socio = await create_socio(client)
    created = await client.post(
        "/api/v1/iscrizioni/", json=iscrizione_payload(socio["id"])
    )
    iscrizione_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/iscrizioni/{iscrizione_id}",
        json={"stato_iscrizione_codice": 2, "quota_partecipazione": 90.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stato_iscrizione_codice"] == 2
    assert data["quota_partecipazione"] == 90.0


@pytest.mark.asyncio
async def test_delete_iscrizione(client: AsyncClient):
    socio = await create_socio(client)
    created = await client.post(
        "/api/v1/iscrizioni/", json=iscrizione_payload(socio["id"])
    )
    iscrizione_id = created.json()["id"]
    response = await client.delete(f"/api/v1/iscrizioni/{iscrizione_id}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/iscrizioni/{iscrizione_id}")).status_code == 404


# ── Auto-flusso lifecycle ─────────────────────────────────────────────────────

CFG_BASE = "/api/v1/configurazione-banda-anno"


async def setup_pagata_env(client: AsyncClient, anno: int = 2026) -> tuple[dict, int]:
    """Seed lookups and create a ConfigurazioneBandaAnno
    with voce_contabilita_quote_id set.

    Returns (cfg_response, codice_pagata).
    """
    await client.post(
        "/api/v1/stati-iscrizione/", json={"codice": 2, "descrizione": "Pagata"}
    )
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Banca"}
    )

    cfg_resp = await client.post(f"{CFG_BASE}/", json={"banda_codice": 1, "anno": anno})
    assert cfg_resp.status_code == 201, cfg_resp.text
    cfg = cfg_resp.json()

    voci_resp = await client.get("/api/v1/voci-contabilita/?banda_codice=1&limit=100")
    voci = voci_resp.json()["items"]
    voce_quote = next(v for v in voci if v["voce_contabilita"] == "Quote associative")

    patch_resp = await client.patch(
        f"{CFG_BASE}/{cfg['id']}",
        json={"voce_contabilita_quote_id": voce_quote["id"]},
    )
    assert patch_resp.status_code == 200, patch_resp.text
    return patch_resp.json(), 2


async def get_auto_flussi(client: AsyncClient) -> list[dict]:
    resp = await client.get("/api/v1/flussi-cassa/")
    assert resp.status_code == 200
    return [f for f in resp.json()["items"] if f["tipo"] == "AUTO_ISCRIZIONE"]


@pytest.mark.asyncio
async def test_create_pagata_creates_auto_flusso(client: AsyncClient):
    _, codice_pagata = await setup_pagata_env(client)
    socio = await create_socio(client)

    response = await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio["id"], stato_iscrizione_codice=codice_pagata),
    )
    assert response.status_code == 201
    iscrizione_id = response.json()["id"]

    flussi = await get_auto_flussi(client)
    assert len(flussi) == 1
    flusso = flussi[0]
    assert flusso["tipo"] == "AUTO_ISCRIZIONE"
    assert flusso["iscrizione_id"] == iscrizione_id
    assert float(flusso["importo"]) == 80.0
    assert "Mario" in flusso["descrizione_operazione"]
    assert "Rossi" in flusso["descrizione_operazione"]
    assert "2026" in flusso["descrizione_operazione"]


@pytest.mark.asyncio
async def test_create_non_pagata_no_flusso(client: AsyncClient):
    await setup_pagata_env(client)
    socio = await create_socio(client)

    response = await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio["id"], stato_iscrizione_codice=1),
    )
    assert response.status_code == 201

    flussi = await get_auto_flussi(client)
    assert len(flussi) == 0


@pytest.mark.asyncio
async def test_update_to_pagata_creates_flusso(client: AsyncClient):
    _, codice_pagata = await setup_pagata_env(client)
    socio = await create_socio(client)

    created = await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio["id"], stato_iscrizione_codice=1),
    )
    assert created.status_code == 201
    iscrizione_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/iscrizioni/{iscrizione_id}",
        json={"stato_iscrizione_codice": codice_pagata},
    )
    assert response.status_code == 200

    flussi = await get_auto_flussi(client)
    assert len(flussi) == 1
    assert flussi[0]["iscrizione_id"] == iscrizione_id


@pytest.mark.asyncio
async def test_update_from_pagata_deletes_flusso(client: AsyncClient):
    _, codice_pagata = await setup_pagata_env(client)
    socio = await create_socio(client)

    created = await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio["id"], stato_iscrizione_codice=codice_pagata),
    )
    assert created.status_code == 201
    iscrizione_id = created.json()["id"]
    assert len(await get_auto_flussi(client)) == 1

    response = await client.patch(
        f"/api/v1/iscrizioni/{iscrizione_id}",
        json={"stato_iscrizione_codice": 1},
    )
    assert response.status_code == 200
    assert len(await get_auto_flussi(client)) == 0


@pytest.mark.asyncio
async def test_update_quota_partecipazione_propagates_to_flusso(client: AsyncClient):
    _, codice_pagata = await setup_pagata_env(client)
    socio = await create_socio(client)

    created = await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio["id"], stato_iscrizione_codice=codice_pagata),
    )
    assert created.status_code == 201
    iscrizione_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/iscrizioni/{iscrizione_id}",
        json={"quota_partecipazione": 120.0},
    )
    assert response.status_code == 200

    flussi = await get_auto_flussi(client)
    assert len(flussi) == 1
    assert float(flussi[0]["importo"]) == 120.0


@pytest.mark.asyncio
async def test_update_data_iscrizione_propagates_to_flusso(client: AsyncClient):
    _, codice_pagata = await setup_pagata_env(client)
    socio = await create_socio(client)

    created = await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio["id"], stato_iscrizione_codice=codice_pagata),
    )
    assert created.status_code == 201
    iscrizione_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/iscrizioni/{iscrizione_id}",
        json={"data_iscrizione": "2026-03-15"},
    )
    assert response.status_code == 200

    flussi = await get_auto_flussi(client)
    assert len(flussi) == 1
    assert "2026-03-15" in flussi[0]["data_registrazione"]


@pytest.mark.asyncio
async def test_delete_iscrizione_deletes_auto_flusso(client: AsyncClient):
    _, codice_pagata = await setup_pagata_env(client)
    socio = await create_socio(client)

    created = await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio["id"], stato_iscrizione_codice=codice_pagata),
    )
    assert created.status_code == 201
    iscrizione_id = created.json()["id"]
    assert len(await get_auto_flussi(client)) == 1

    response = await client.delete(f"/api/v1/iscrizioni/{iscrizione_id}")
    assert response.status_code == 204
    assert len(await get_auto_flussi(client)) == 0


@pytest.mark.asyncio
async def test_create_pagata_without_voce_quote_422(client: AsyncClient):
    await client.post(
        "/api/v1/stati-iscrizione/", json={"codice": 2, "descrizione": "Pagata"}
    )
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Banca"}
    )
    # Create cfg WITHOUT linking voce_contabilita_quote_id
    cfg_resp = await client.post(f"{CFG_BASE}/", json={"banda_codice": 1, "anno": 2026})
    assert cfg_resp.status_code == 201
    assert cfg_resp.json()["voce_contabilita_quote"] is None

    socio = await create_socio(client)
    response = await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio["id"], stato_iscrizione_codice=2),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_pagata_without_config_422(client: AsyncClient):
    await client.post(
        "/api/v1/stati-iscrizione/", json={"codice": 2, "descrizione": "Pagata"}
    )
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Banca"}
    )
    # No configurazione_banda_anno created at all

    socio = await create_socio(client)
    response = await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio["id"], stato_iscrizione_codice=2),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_pagata_anno_chiuso_409(client: AsyncClient):
    cfg, codice_pagata = await setup_pagata_env(client)

    close_resp = await client.post(f"{CFG_BASE}/{cfg['id']}/chiudi")
    assert close_resp.status_code == 200

    socio = await create_socio(client)
    response = await client.post(
        "/api/v1/iscrizioni/",
        json=iscrizione_payload(socio["id"], stato_iscrizione_codice=codice_pagata),
    )
    assert response.status_code == 409

    # Iscrizione must NOT have been persisted
    iscrizioni_resp = await client.get("/api/v1/iscrizioni/")
    assert iscrizioni_resp.json()["meta"]["total_items"] == 0
