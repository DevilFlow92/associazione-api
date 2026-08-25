from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_persona(client: AsyncClient, banda_codice: int = 1) -> dict:
    response = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": banda_codice, "nome": "Mario", "cognome": "Rossi"},
    )
    return response.json()


def socio_payload(persona_id: int, **overrides) -> dict:
    payload = {
        "persona_id": persona_id,
        "ruolo_banda_codice": 10,
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_socio(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    assert response.status_code == 201
    data = response.json()
    assert data["persona_id"] == persona["id"]
    assert data["codice_socio"] == "00001"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_socio_persona_not_found(client: AsyncClient):
    response = await client.post("/api/v1/soci/", json=socio_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_socio_codice_client_ignorato(client: AsyncClient):
    """Il codice_socio nel payload di creazione viene ignorato: il server
    assegna sempre il proprio valore calcolato, mai quello del client."""
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/soci/", json=socio_payload(persona["id"], codice_socio="ZZZZZ")
    )
    assert response.status_code == 201
    assert response.json()["codice_socio"] == "00001"


@pytest.mark.asyncio
async def test_create_socio_sequenza_incrementale(client: AsyncClient):
    persona = await create_persona(client)
    primo = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    secondo = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    assert primo.json()["codice_socio"] == "00001"
    assert secondo.json()["codice_socio"] == "00002"


@pytest.mark.asyncio
async def test_create_socio_colma_buco_nella_sequenza(client: AsyncClient):
    persona = await create_persona(client)
    primo = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    secondo = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    terzo = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    assert [
        primo.json()["codice_socio"],
        secondo.json()["codice_socio"],
        terzo.json()["codice_socio"],
    ] == ["00001", "00002", "00003"]

    delete_response = await client.delete(f"/api/v1/soci/{secondo.json()['id']}")
    assert delete_response.status_code == 204

    quarto = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    assert quarto.json()["codice_socio"] == "00002"


@pytest.mark.asyncio
async def test_create_socio_bande_diverse_ripartono_da_zero(client: AsyncClient):
    persona_banda_1 = await create_persona(client, banda_codice=1)
    persona_banda_2 = await create_persona(client, banda_codice=2)

    await client.post("/api/v1/soci/", json=socio_payload(persona_banda_1["id"]))
    secondo_banda_1 = await client.post(
        "/api/v1/soci/", json=socio_payload(persona_banda_1["id"])
    )
    primo_banda_2 = await client.post(
        "/api/v1/soci/", json=socio_payload(persona_banda_2["id"])
    )

    assert secondo_banda_1.json()["codice_socio"] == "00002"
    assert primo_banda_2.json()["codice_socio"] == "00001"


@pytest.mark.asyncio
async def test_create_socio_ignora_codice_non_numerico_in_sequenza(
    client: AsyncClient,
):
    """Un codice non puramente numerico (correzione manuale via PATCH) non
    fa parte della sequenza progressiva: non blocca né sposta il prossimo
    numero libero, che continua a considerare solo i codici numerici."""
    persona = await create_persona(client)
    primo = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    secondo = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    assert primo.json()["codice_socio"] == "00001"
    assert secondo.json()["codice_socio"] == "00002"

    patch_response = await client.patch(
        f"/api/v1/soci/{secondo.json()['id']}", json={"codice_socio": "ABCDE"}
    )
    assert patch_response.status_code == 200

    terzo = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    assert terzo.json()["codice_socio"] == "00002"


@pytest.mark.asyncio
async def test_update_socio_codice_troppo_lungo(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    response = await client.patch(
        f"/api/v1/soci/{created.json()['id']}",
        json={"codice_socio": "000001"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_socio_not_found(client: AsyncClient):
    response = await client.get("/api/v1/soci/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_soci_empty(client: AsyncClient):
    response = await client.get("/api/v1/soci/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0
    assert data["meta"]["page"] == 1


@pytest.mark.asyncio
async def test_update_socio(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    socio_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/soci/{socio_id}", json={"ruolo_banda_codice": 1}
    )
    assert response.status_code == 200
    assert response.json()["ruolo_banda_codice"] == 1


@pytest.mark.asyncio
async def test_update_socio_codice_duplicato(client: AsyncClient):
    persona = await create_persona(client)
    primo = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    secondo = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    response = await client.patch(
        f"/api/v1/soci/{secondo.json()['id']}",
        json={"codice_socio": primo.json()["codice_socio"]},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_socio(client: AsyncClient):
    persona = await create_persona(client)
    created = await client.post("/api/v1/soci/", json=socio_payload(persona["id"]))
    socio_id = created.json()["id"]
    response = await client.delete(f"/api/v1/soci/{socio_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/soci/{socio_id}")
    assert response.status_code == 404
