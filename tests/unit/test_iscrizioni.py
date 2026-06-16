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
