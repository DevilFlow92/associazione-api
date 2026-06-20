from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.models.flusso_cassa import TipoFlussoCassa


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
