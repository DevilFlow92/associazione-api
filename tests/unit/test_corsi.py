from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_tipo_corso(
    client: AsyncClient, codice: int = 1, descrizione: str = "Ottoni"
) -> dict:
    response = await client.post(
        "/api/v1/tipi-corso/", json={"codice": codice, "descrizione": descrizione}
    )
    assert response.status_code == 201
    return response.json()


async def create_persona(
    client: AsyncClient, nome: str = "Mario", cognome: str = "Rossi"
) -> dict:
    response = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": nome, "cognome": cognome},
    )
    assert response.status_code == 201
    return response.json()


def corso_payload(tipo_corso_codice: int, **overrides) -> dict:
    payload = {
        "banda_codice": 1,
        "tipo_corso_codice": tipo_corso_codice,
        "anno": 2026,
    }
    payload.update(overrides)
    return payload


async def create_corso(
    client: AsyncClient, tipo_corso_codice: int, **overrides
) -> dict:
    response = await client.post(
        "/api/v1/corsi/", json=corso_payload(tipo_corso_codice, **overrides)
    )
    assert response.status_code == 201
    return response.json()


# ── TipoCorso (lookup) ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_tipo_corso(client: AsyncClient):
    tipo = await create_tipo_corso(client, codice=2, descrizione="Percussioni")
    assert tipo["codice"] == 2
    assert tipo["descrizione"] == "Percussioni"

    response = await client.get("/api/v1/tipi-corso/2")
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Percussioni"


@pytest.mark.asyncio
async def test_list_tipi_corso(client: AsyncClient):
    await create_tipo_corso(client, codice=1, descrizione="Ottoni")
    await create_tipo_corso(client, codice=2, descrizione="Percussioni")

    response = await client.get("/api/v1/tipi-corso/")
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2


@pytest.mark.asyncio
async def test_get_tipo_corso_not_found(client: AsyncClient):
    response = await client.get("/api/v1/tipi-corso/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_tipo_corso_codice_duplicato(client: AsyncClient):
    await create_tipo_corso(client, codice=1, descrizione="Ottoni")
    response = await client.post(
        "/api/v1/tipi-corso/", json={"codice": 1, "descrizione": "Altro"}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_and_delete_tipo_corso(client: AsyncClient):
    await create_tipo_corso(client, codice=1, descrizione="Ottoni")

    response = await client.patch(
        "/api/v1/tipi-corso/1", json={"descrizione": "Ottoni e ance"}
    )
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Ottoni e ance"

    response = await client.delete("/api/v1/tipi-corso/1")
    assert response.status_code == 204
    assert (await client.get("/api/v1/tipi-corso/1")).status_code == 404


# ── CRUD Corso ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_corso_minimo(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    response = await client.post("/api/v1/corsi/", json=corso_payload(tipo["codice"]))
    assert response.status_code == 201
    data = response.json()
    assert data["anno"] == 2026
    assert data["tipo_corso"]["descrizione"] == "Ottoni"
    assert data["coordinatore"] is None
    assert data["insegnante"] is None


@pytest.mark.asyncio
async def test_create_corso_con_coordinatore_e_insegnante(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    coordinatore = await create_persona(client, "Anna", "Bianchi")
    insegnante = await create_persona(client, "Luca", "Verdi")

    corso = await create_corso(
        client,
        tipo["codice"],
        coordinatore_persona_id=coordinatore["id"],
        insegnante_persona_id=insegnante["id"],
    )
    assert corso["coordinatore"]["cognome"] == "Bianchi"
    assert corso["insegnante"]["cognome"] == "Verdi"


@pytest.mark.asyncio
async def test_create_corso_tipo_corso_not_found(client: AsyncClient):
    response = await client.post("/api/v1/corsi/", json=corso_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_corso_coordinatore_not_found(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    response = await client.post(
        "/api/v1/corsi/",
        json=corso_payload(tipo["codice"], coordinatore_persona_id=999),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_corso_insegnante_not_found(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    response = await client.post(
        "/api/v1/corsi/",
        json=corso_payload(tipo["codice"], insegnante_persona_id=999),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_corso_not_found(client: AsyncClient):
    response = await client.get("/api/v1/corsi/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_corso(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    corso = await create_corso(client, tipo["codice"])

    response = await client.patch(
        f"/api/v1/corsi/{corso['id']}", json={"note": "Iscrizioni aperte"}
    )
    assert response.status_code == 200
    assert response.json()["note"] == "Iscrizioni aperte"


@pytest.mark.asyncio
async def test_update_corso_assegna_insegnante(client: AsyncClient):
    """Regressione sul pattern già noto in ProvaRepository/ServizioRepository:
    la sessione usa expire_on_commit=False, quindi senza un expire esplicito
    la rilettura post-update restituirebbe l'insegnante stantio (None)."""
    tipo = await create_tipo_corso(client)
    corso = await create_corso(client, tipo["codice"])
    assert corso["insegnante"] is None
    insegnante = await create_persona(client, "Luca", "Verdi")

    response = await client.patch(
        f"/api/v1/corsi/{corso['id']}",
        json={"insegnante_persona_id": insegnante["id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["insegnante"] is not None
    assert data["insegnante"]["id"] == insegnante["id"]


@pytest.mark.asyncio
async def test_update_corso_not_found(client: AsyncClient):
    response = await client.patch("/api/v1/corsi/999", json={"note": "x"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_corso_insegnante_not_found(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    corso = await create_corso(client, tipo["codice"])
    response = await client.patch(
        f"/api/v1/corsi/{corso['id']}", json={"insegnante_persona_id": 999}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_corso(client: AsyncClient):
    tipo = await create_tipo_corso(client)
    corso = await create_corso(client, tipo["codice"])

    response = await client.delete(f"/api/v1/corsi/{corso['id']}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/corsi/{corso['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_corso_not_found(client: AsyncClient):
    response = await client.delete("/api/v1/corsi/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_corsi_filtri(client: AsyncClient):
    tipo_ottoni = await create_tipo_corso(client, codice=1, descrizione="Ottoni")
    tipo_percussioni = await create_tipo_corso(
        client, codice=2, descrizione="Percussioni"
    )
    await create_corso(client, tipo_ottoni["codice"], anno=2026)
    await create_corso(client, tipo_percussioni["codice"], anno=2026)
    await create_corso(client, tipo_ottoni["codice"], anno=2025)

    response = await client.get(
        "/api/v1/corsi/",
        params={"anno": 2026, "tipo_corso_codice": tipo_ottoni["codice"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["anno"] == 2026
    assert data["items"][0]["tipo_corso_codice"] == tipo_ottoni["codice"]


@pytest.mark.asyncio
async def test_list_corsi_corsi_paralleli_stesso_tipo_e_anno_ammessi(
    client: AsyncClient,
):
    """Non c'è vincolo di unicità (tipo_corso_codice, anno, banda_codice):
    due corsi paralleli dello stesso tipo nello stesso anno (es. livelli
    diversi con insegnanti diversi) sono un caso di dominio legittimo."""
    tipo = await create_tipo_corso(client)
    await create_corso(client, tipo["codice"], anno=2026, note="Livello base")
    await create_corso(client, tipo["codice"], anno=2026, note="Livello avanzato")

    response = await client.get(
        "/api/v1/corsi/", params={"anno": 2026, "tipo_corso_codice": tipo["codice"]}
    )
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2
