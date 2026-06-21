from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.models.flusso_cassa import TipoFlussoCassa

CFG_BASE = "/api/v1/configurazione-banda-anno"


async def create_voce(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/voci-contabilita/",
        json={
            "banda_codice": 1,
            "voce_contabilita": "Quote associative",
            "sezione_rendiconto_codice": 2,
            "voce_rendiconto_codice": 2,
            "sottovoce_rendiconto_codice": 6,
        },
    )
    return response.json()


def flusso_payload(voce_id: int, **overrides) -> dict:
    payload = {
        "data_registrazione": "2026-01-15T00:00:00",
        "descrizione_operazione": "Incasso quota socio",
        "voce_contabilita_id": voce_id,
        "importo": 50.00,
        "segno": "+",
        "natura_flusso_codice": 1,
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_flusso_cassa(client: AsyncClient):
    voce = await create_voce(client)
    response = await client.post(
        "/api/v1/flussi-cassa/", json=flusso_payload(voce["id"])
    )
    assert response.status_code == 201
    data = response.json()
    assert data["voce_contabilita_id"] == voce["id"]
    assert data["importo"] == 50.00
    assert data["segno"] == "+"


@pytest.mark.asyncio
async def test_create_flusso_voce_not_found(client: AsyncClient):
    response = await client.post("/api/v1/flussi-cassa/", json=flusso_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_flusso_not_found(client: AsyncClient):
    response = await client.get("/api/v1/flussi-cassa/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_flussi_by_voce(client: AsyncClient):
    voce = await create_voce(client)
    await client.post("/api/v1/flussi-cassa/", json=flusso_payload(voce["id"]))
    await client.post(
        "/api/v1/flussi-cassa/",
        json=flusso_payload(voce["id"], descrizione_operazione="Altra quota"),
    )
    response = await client.get(f"/api/v1/flussi-cassa/voce-contabilita/{voce['id']}")
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2


@pytest.mark.asyncio
async def test_get_flussi_by_voce_not_found(client: AsyncClient):
    response = await client.get("/api/v1/flussi-cassa/voce-contabilita/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_flusso_cassa(client: AsyncClient):
    voce = await create_voce(client)
    created = await client.post(
        "/api/v1/flussi-cassa/", json=flusso_payload(voce["id"])
    )
    flusso_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/flussi-cassa/{flusso_id}", json={"importo": 75.0}
    )
    assert response.status_code == 200
    assert response.json()["importo"] == 75.0


@pytest.mark.asyncio
async def test_delete_flusso_cassa(client: AsyncClient):
    voce = await create_voce(client)
    created = await client.post(
        "/api/v1/flussi-cassa/", json=flusso_payload(voce["id"])
    )
    flusso_id = created.json()["id"]
    response = await client.delete(f"/api/v1/flussi-cassa/{flusso_id}")
    assert response.status_code == 204
    response = await client.get(f"/api/v1/flussi-cassa/{flusso_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_default_tipo_is_movimento(client: AsyncClient):
    voce = await create_voce(client)
    response = await client.post(
        "/api/v1/flussi-cassa/", json=flusso_payload(voce["id"])
    )
    assert response.status_code == 201
    assert response.json()["tipo"] == TipoFlussoCassa.MOVIMENTO


@pytest.mark.asyncio
@pytest.mark.parametrize("tipo", list(TipoFlussoCassa))
async def test_create_with_tipo(client: AsyncClient, tipo: TipoFlussoCassa):
    voce = await create_voce(client)
    response = await client.post(
        "/api/v1/flussi-cassa/", json=flusso_payload(voce["id"], tipo=tipo.value)
    )
    assert response.status_code == 201
    assert response.json()["tipo"] == tipo


async def _create_iscrizione(client: AsyncClient) -> dict:
    persona = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": "Giulia", "cognome": "Bianchi"},
    )
    socio = await client.post(
        "/api/v1/soci/",
        json={
            "persona_id": persona.json()["id"],
            "codice_socio": "S099",
            "banda_codice": 1,
            "ruolo_banda_codice": 10,
        },
    )
    iscrizione = await client.post(
        "/api/v1/iscrizioni/",
        json={
            "socio_id": socio.json()["id"],
            "anno": 2026,
            "quota_partecipazione": 80.0,
            "stato_iscrizione_codice": 1,
            "data_iscrizione": "2026-01-10",
        },
    )
    assert iscrizione.status_code == 201
    return iscrizione.json()


@pytest.mark.asyncio
async def test_flusso_cassa_optional_iscrizione_id(client: AsyncClient):
    voce = await create_voce(client)
    iscrizione = await _create_iscrizione(client)
    response = await client.post(
        "/api/v1/flussi-cassa/",
        json=flusso_payload(voce["id"], iscrizione_id=iscrizione["id"]),
    )
    assert response.status_code == 201
    assert response.json()["iscrizione_id"] == iscrizione["id"]


@pytest.mark.asyncio
async def test_flusso_cassa_optional_trasferimento_id(client: AsyncClient):
    voce = await create_voce(client)
    tid = str(uuid.uuid4())
    response = await client.post(
        "/api/v1/flussi-cassa/",
        json=flusso_payload(voce["id"], trasferimento_id=tid),
    )
    assert response.status_code == 201
    assert response.json()["trasferimento_id"] == tid


# ── Anno chiuso enforcement tests ────────────────────────────────────────────


async def _create_cfg_and_close(
    client: AsyncClient, banda_codice: int, anno: int
) -> dict:
    """Create a ConfigurazioneBandaAnno and close it via /chiudi."""
    cfg_resp = await client.post(
        f"{CFG_BASE}/",
        json={"banda_codice": banda_codice, "anno": anno},
    )
    assert cfg_resp.status_code == 201, cfg_resp.text
    cfg = cfg_resp.json()
    close_resp = await client.post(f"{CFG_BASE}/{cfg['id']}/chiudi")
    assert close_resp.status_code == 200, close_resp.text
    return close_resp.json()


@pytest.mark.asyncio
async def test_create_flusso_blocked_when_anno_chiuso(client: AsyncClient):
    voce = await create_voce(client)
    # The voce was seeded for banda_codice=1; close anno 2026
    await _create_cfg_and_close(client, banda_codice=1, anno=2026)
    response = await client.post(
        "/api/v1/flussi-cassa/",
        json=flusso_payload(voce["id"], data_registrazione="2026-03-01T00:00:00"),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_flusso_blocked_when_anno_chiuso(client: AsyncClient):
    voce = await create_voce(client)
    created = await client.post(
        "/api/v1/flussi-cassa/",
        json=flusso_payload(voce["id"], data_registrazione="2026-03-01T00:00:00"),
    )
    assert created.status_code == 201
    flusso_id = created.json()["id"]
    await _create_cfg_and_close(client, banda_codice=1, anno=2026)
    response = await client.patch(
        f"/api/v1/flussi-cassa/{flusso_id}", json={"importo": 99.0}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_flusso_blocked_when_anno_chiuso(client: AsyncClient):
    voce = await create_voce(client)
    created = await client.post(
        "/api/v1/flussi-cassa/",
        json=flusso_payload(voce["id"], data_registrazione="2026-03-01T00:00:00"),
    )
    assert created.status_code == 201
    flusso_id = created.json()["id"]
    await _create_cfg_and_close(client, banda_codice=1, anno=2026)
    response = await client.delete(f"/api/v1/flussi-cassa/{flusso_id}")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_flusso_works_for_different_anno(client: AsyncClient):
    voce = await create_voce(client)
    await _create_cfg_and_close(client, banda_codice=1, anno=2024)
    # 2025 is open — should succeed
    response = await client.post(
        "/api/v1/flussi-cassa/",
        json=flusso_payload(voce["id"], data_registrazione="2025-06-01T00:00:00"),
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_update_data_to_chiuso_anno_blocked(client: AsyncClient):
    voce = await create_voce(client)
    # Create flusso in 2025 (open)
    created = await client.post(
        "/api/v1/flussi-cassa/",
        json=flusso_payload(voce["id"], data_registrazione="2025-06-01T00:00:00"),
    )
    assert created.status_code == 201
    flusso_id = created.json()["id"]
    # Close 2024
    await _create_cfg_and_close(client, banda_codice=1, anno=2024)
    # Try to move flusso into the closed year
    response = await client.patch(
        f"/api/v1/flussi-cassa/{flusso_id}",
        json={"data_registrazione": "2024-12-31T00:00:00"},
    )
    assert response.status_code == 409


# ── Trasferimenti atomici cassa↔banca ────────────────────────────────────────

TRASF_BASE = "/api/v1/flussi-cassa/trasferimenti/"


async def _create_natura(client: AsyncClient, codice: int, descrizione: str) -> dict:
    resp = await client.post(
        "/api/v1/nature-flusso/",
        json={"codice": codice, "descrizione": descrizione},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_nature_cassa_banca(client: AsyncClient) -> None:
    await _create_natura(client, 1, "Cassa")
    await _create_natura(client, 2, "Banca")


def trasferimento_payload(voce_id: int, **overrides) -> dict:
    payload = {
        "data_registrazione": "2026-02-01T00:00:00",
        "importo": 195.00,
        "natura_da_codice": 1,
        "natura_a_codice": 2,
        "voce_contabilita_id": voce_id,
        "descrizione_operazione": "Versamento in banca",
        "note": None,
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_crea_trasferimento_ok(client: AsyncClient):
    voce = await create_voce(client)
    await _create_nature_cassa_banca(client)
    response = await client.post(TRASF_BASE, json=trasferimento_payload(voce["id"]))
    assert response.status_code == 201, response.text
    flussi = response.json()["flussi"]
    assert len(flussi) == 2
    uscita, entrata = flussi
    # Stessa coppia: identico trasferimento_id e importo, segno/tipo opposti.
    assert uscita["trasferimento_id"] is not None
    assert uscita["trasferimento_id"] == entrata["trasferimento_id"]
    assert uscita["importo"] == entrata["importo"] == 195.00
    assert uscita["tipo"] == TipoFlussoCassa.TRASFERIMENTO_USCITA
    assert uscita["segno"] == "-"
    assert uscita["natura_flusso_codice"] == 1
    assert entrata["tipo"] == TipoFlussoCassa.TRASFERIMENTO_ENTRATA
    assert entrata["segno"] == "+"
    assert entrata["natura_flusso_codice"] == 2


@pytest.mark.asyncio
async def test_crea_trasferimento_natura_uguale_422(client: AsyncClient):
    voce = await create_voce(client)
    await _create_nature_cassa_banca(client)
    response = await client.post(
        TRASF_BASE,
        json=trasferimento_payload(voce["id"], natura_da_codice=1, natura_a_codice=1),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_crea_trasferimento_voce_non_trovata_404(client: AsyncClient):
    await _create_nature_cassa_banca(client)
    response = await client.post(TRASF_BASE, json=trasferimento_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_crea_trasferimento_anno_chiuso_409(client: AsyncClient):
    voce = await create_voce(client)
    await _create_nature_cassa_banca(client)
    await _create_cfg_and_close(client, banda_codice=1, anno=2026)
    response = await client.post(
        TRASF_BASE,
        json=trasferimento_payload(
            voce["id"], data_registrazione="2026-02-01T00:00:00"
        ),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize("importo", [0, -100])
async def test_crea_trasferimento_importo_zero_o_negativo_422(
    client: AsyncClient, importo: int
):
    voce = await create_voce(client)
    await _create_nature_cassa_banca(client)
    response = await client.post(
        TRASF_BASE, json=trasferimento_payload(voce["id"], importo=importo)
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_uscita_elimina_anche_entrata(client: AsyncClient):
    voce = await create_voce(client)
    await _create_nature_cassa_banca(client)
    created = await client.post(TRASF_BASE, json=trasferimento_payload(voce["id"]))
    uscita, entrata = created.json()["flussi"]

    response = await client.delete(f"/api/v1/flussi-cassa/{uscita['id']}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/flussi-cassa/{uscita['id']}")).status_code == 404
    assert (
        await client.get(f"/api/v1/flussi-cassa/{entrata['id']}")
    ).status_code == 404


@pytest.mark.asyncio
async def test_delete_entrata_elimina_anche_uscita(client: AsyncClient):
    voce = await create_voce(client)
    await _create_nature_cassa_banca(client)
    created = await client.post(TRASF_BASE, json=trasferimento_payload(voce["id"]))
    uscita, entrata = created.json()["flussi"]

    response = await client.delete(f"/api/v1/flussi-cassa/{entrata['id']}")
    assert response.status_code == 204
    assert (
        await client.get(f"/api/v1/flussi-cassa/{entrata['id']}")
    ).status_code == 404
    assert (await client.get(f"/api/v1/flussi-cassa/{uscita['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_update_flusso_trasferimento_409(client: AsyncClient):
    voce = await create_voce(client)
    await _create_nature_cassa_banca(client)
    created = await client.post(TRASF_BASE, json=trasferimento_payload(voce["id"]))
    uscita = created.json()["flussi"][0]

    response = await client.patch(
        f"/api/v1/flussi-cassa/{uscita['id']}", json={"importo": 10.0}
    )
    assert response.status_code == 409
