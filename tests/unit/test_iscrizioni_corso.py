from __future__ import annotations

from collections.abc import Collection

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user
from app.models.permesso import Permesso
from app.models.ruolo import Ruolo
from app.models.utente import TipoUtente, Utente
from main import app


def _user(*, superuser: bool = False, permessi: Collection[str] = ()) -> Utente:
    ruoli: list[Ruolo] = []
    if permessi:
        ruoli = [
            Ruolo(
                nome="test",
                permessi=[Permesso(codice=c, descrizione=c) for c in permessi],
            )
        ]
    return Utente(
        id=1,
        tipo=TipoUtente.UMANO,
        email="test@example.com",
        superuser=superuser,
        ruoli=ruoli,
    )


async def create_tipo_corso(
    client: AsyncClient, codice: int = 1, descrizione: str = "Ottoni"
) -> dict:
    response = await client.post(
        "/api/v1/tipi-corso/", json={"codice": codice, "descrizione": descrizione}
    )
    assert response.status_code == 201
    return response.json()


async def create_corso(
    client: AsyncClient, tipo_corso_codice: int = 1, **overrides
) -> dict:
    tipo = await create_tipo_corso(client, codice=tipo_corso_codice)
    payload = {"banda_codice": 1, "tipo_corso_codice": tipo["codice"], "anno": 2026}
    payload.update(overrides)
    response = await client.post("/api/v1/corsi/", json=payload)
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


async def create_stato(
    client: AsyncClient, codice: int = 1, descrizione: str = "Richiesta"
) -> dict:
    response = await client.post(
        "/api/v1/stati-iscrizione-corso/",
        json={"codice": codice, "descrizione": descrizione},
    )
    assert response.status_code == 201
    return response.json()


def pdf_file(filename: str = "modulo.pdf") -> tuple[str, tuple[str, bytes, str]]:
    return ("file", (filename, b"%PDF-1.4 modulo", "application/pdf"))


async def upload_documento(client: AsyncClient, filename: str = "modulo.pdf") -> dict:
    response = await client.post("/api/v1/documenti/", files=[pdf_file(filename)])
    assert response.status_code == 201
    return response.json()


def iscrizione_corso_payload(
    corso_id: int, persona_id: int, stato_codice: int, **overrides
) -> dict:
    payload = {
        "corso_id": corso_id,
        "persona_id": persona_id,
        "stato_iscrizione_corso_codice": stato_codice,
        "data_iscrizione": "2026-09-01",
    }
    payload.update(overrides)
    return payload


async def create_iscrizione_corso(
    client: AsyncClient, corso_id: int, persona_id: int, stato_codice: int, **overrides
) -> dict:
    response = await client.post(
        "/api/v1/iscrizioni-corso/",
        json=iscrizione_corso_payload(corso_id, persona_id, stato_codice, **overrides),
    )
    assert response.status_code == 201
    return response.json()


# ── StatoIscrizioneCorso (lookup) ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_stato_iscrizione_corso(client: AsyncClient):
    stato = await create_stato(client, codice=2, descrizione="Confermata")
    assert stato["codice"] == 2
    assert stato["descrizione"] == "Confermata"

    response = await client.get("/api/v1/stati-iscrizione-corso/2")
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Confermata"


@pytest.mark.asyncio
async def test_list_stati_iscrizione_corso(client: AsyncClient):
    await create_stato(client, codice=1, descrizione="Richiesta")
    await create_stato(client, codice=2, descrizione="Confermata")

    response = await client.get("/api/v1/stati-iscrizione-corso/")
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2


@pytest.mark.asyncio
async def test_get_stato_iscrizione_corso_not_found(client: AsyncClient):
    response = await client.get("/api/v1/stati-iscrizione-corso/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_stato_iscrizione_corso_codice_duplicato(client: AsyncClient):
    await create_stato(client, codice=1, descrizione="Richiesta")
    response = await client.post(
        "/api/v1/stati-iscrizione-corso/", json={"codice": 1, "descrizione": "Altro"}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_and_delete_stato_iscrizione_corso(client: AsyncClient):
    await create_stato(client, codice=1, descrizione="Richiesta")

    response = await client.patch(
        "/api/v1/stati-iscrizione-corso/1", json={"descrizione": "Richiesta ricevuta"}
    )
    assert response.status_code == 200
    assert response.json()["descrizione"] == "Richiesta ricevuta"

    response = await client.delete("/api/v1/stati-iscrizione-corso/1")
    assert response.status_code == 204
    assert (await client.get("/api/v1/stati-iscrizione-corso/1")).status_code == 404


# ── CRUD IscrizioneCorso ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_iscrizione_corso_minima(client: AsyncClient):
    corso = await create_corso(client)
    persona = await create_persona(client)
    stato = await create_stato(client)

    response = await client.post(
        "/api/v1/iscrizioni-corso/",
        json=iscrizione_corso_payload(corso["id"], persona["id"], stato["codice"]),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["corso_id"] == corso["id"]
    assert data["corso"]["id"] == corso["id"]
    assert data["corso"]["tipo_corso"]["descrizione"] == "Ottoni"
    assert data["persona_id"] == persona["id"]
    assert data["persona"]["cognome"] == "Rossi"
    assert data["stato_iscrizione_corso"]["descrizione"] == "Richiesta"
    assert data["documento_id"] is None
    assert data["documento"] is None


@pytest.mark.asyncio
async def test_create_iscrizione_corso_con_documento(client: AsyncClient):
    corso = await create_corso(client)
    persona = await create_persona(client)
    stato = await create_stato(client)
    doc = await upload_documento(client)

    iscrizione = await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato["codice"], documento_id=doc["id"]
    )
    assert iscrizione["documento_id"] == doc["id"]
    assert iscrizione["documento"] is not None


@pytest.mark.asyncio
async def test_create_iscrizione_corso_persona_puo_reiscriversi(client: AsyncClient):
    """Nessun vincolo di unicità (persona_id, corso_id): una persona può
    essere re-iscritta allo stesso corso dopo un'iscrizione annullata."""
    corso = await create_corso(client)
    persona = await create_persona(client)
    stato_annullata = await create_stato(client, codice=3, descrizione="Annullata")
    stato_richiesta = await create_stato(client, codice=1, descrizione="Richiesta")

    await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato_annullata["codice"]
    )
    seconda = await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato_richiesta["codice"]
    )
    assert seconda["corso_id"] == corso["id"]
    assert seconda["persona_id"] == persona["id"]


@pytest.mark.asyncio
async def test_create_iscrizione_corso_corso_not_found(client: AsyncClient):
    persona = await create_persona(client)
    stato = await create_stato(client)
    response = await client.post(
        "/api/v1/iscrizioni-corso/",
        json=iscrizione_corso_payload(999, persona["id"], stato["codice"]),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_iscrizione_corso_persona_not_found(client: AsyncClient):
    corso = await create_corso(client)
    stato = await create_stato(client)
    response = await client.post(
        "/api/v1/iscrizioni-corso/",
        json=iscrizione_corso_payload(corso["id"], 999, stato["codice"]),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_iscrizione_corso_stato_not_found(client: AsyncClient):
    corso = await create_corso(client)
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/iscrizioni-corso/",
        json=iscrizione_corso_payload(corso["id"], persona["id"], 999),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_iscrizione_corso_documento_not_found(client: AsyncClient):
    corso = await create_corso(client)
    persona = await create_persona(client)
    stato = await create_stato(client)
    response = await client.post(
        "/api/v1/iscrizioni-corso/",
        json=iscrizione_corso_payload(
            corso["id"], persona["id"], stato["codice"], documento_id=999
        ),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_iscrizione_corso_not_found(client: AsyncClient):
    response = await client.get("/api/v1/iscrizioni-corso/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_iscrizione_corso(client: AsyncClient):
    corso = await create_corso(client)
    persona = await create_persona(client)
    stato = await create_stato(client)
    iscrizione = await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato["codice"]
    )

    response = await client.patch(
        f"/api/v1/iscrizioni-corso/{iscrizione['id']}",
        json={"note": "Attesa conferma pagamento"},
    )
    assert response.status_code == 200
    assert response.json()["note"] == "Attesa conferma pagamento"


@pytest.mark.asyncio
async def test_update_iscrizione_corso_cambia_stato(client: AsyncClient):
    corso = await create_corso(client)
    persona = await create_persona(client)
    stato_richiesta = await create_stato(client, codice=1, descrizione="Richiesta")
    stato_confermata = await create_stato(client, codice=2, descrizione="Confermata")
    iscrizione = await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato_richiesta["codice"]
    )

    response = await client.patch(
        f"/api/v1/iscrizioni-corso/{iscrizione['id']}",
        json={"stato_iscrizione_corso_codice": stato_confermata["codice"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stato_iscrizione_corso"]["descrizione"] == "Confermata"


@pytest.mark.asyncio
async def test_update_iscrizione_corso_aggiunge_documento(client: AsyncClient):
    """Stesso pattern di regressione già noto per Prova/Corso/Lezione: la
    sessione usa expire_on_commit=False, quindi senza expire esplicito la
    rilettura post-update restituirebbe il documento stantio (None)."""
    corso = await create_corso(client)
    persona = await create_persona(client)
    stato = await create_stato(client)
    iscrizione = await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato["codice"]
    )
    assert iscrizione["documento_id"] is None
    doc = await upload_documento(client)

    response = await client.patch(
        f"/api/v1/iscrizioni-corso/{iscrizione['id']}",
        json={"documento_id": doc["id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["documento_id"] == doc["id"]
    assert data["documento"] is not None


@pytest.mark.asyncio
async def test_update_iscrizione_corso_not_found(client: AsyncClient):
    response = await client.patch("/api/v1/iscrizioni-corso/999", json={"note": "x"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_iscrizione_corso_stato_not_found(client: AsyncClient):
    corso = await create_corso(client)
    persona = await create_persona(client)
    stato = await create_stato(client)
    iscrizione = await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato["codice"]
    )

    response = await client.patch(
        f"/api/v1/iscrizioni-corso/{iscrizione['id']}",
        json={"stato_iscrizione_corso_codice": 999},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_iscrizione_corso(client: AsyncClient):
    corso = await create_corso(client)
    persona = await create_persona(client)
    stato = await create_stato(client)
    iscrizione = await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato["codice"]
    )

    response = await client.delete(f"/api/v1/iscrizioni-corso/{iscrizione['id']}")
    assert response.status_code == 204
    assert (
        await client.get(f"/api/v1/iscrizioni-corso/{iscrizione['id']}")
    ).status_code == 404


@pytest.mark.asyncio
async def test_delete_iscrizione_corso_not_found(client: AsyncClient):
    response = await client.delete("/api/v1/iscrizioni-corso/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_iscrizioni_corso_filtro_corso_e_persona(client: AsyncClient):
    corso1 = await create_corso(client, tipo_corso_codice=1)
    corso2 = await create_corso(client, tipo_corso_codice=2, anno=2025)
    persona1 = await create_persona(client, "Mario", "Rossi")
    persona2 = await create_persona(client, "Anna", "Bianchi")
    stato = await create_stato(client)

    await create_iscrizione_corso(client, corso1["id"], persona1["id"], stato["codice"])
    await create_iscrizione_corso(client, corso1["id"], persona2["id"], stato["codice"])
    await create_iscrizione_corso(client, corso2["id"], persona1["id"], stato["codice"])

    response = await client.get(
        "/api/v1/iscrizioni-corso/", params={"corso_id": corso1["id"]}
    )
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2

    response = await client.get(
        "/api/v1/iscrizioni-corso/", params={"persona_id": persona1["id"]}
    )
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2

    response = await client.get(
        "/api/v1/iscrizioni-corso/",
        params={"corso_id": corso1["id"], "persona_id": persona1["id"]},
    )
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 1


# ── RBAC router iscrizioni-corso ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_iscrizioni_corso_forbidden_without_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user()
    response = await client.get("/api/v1/iscrizioni-corso/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_iscrizioni_corso_succeeds_with_corsi_read_permission(
    client: AsyncClient,
):
    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.get("/api/v1/iscrizioni-corso/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_iscrizione_corso_forbidden_without_write_permission(
    client: AsyncClient,
):
    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.post(
        "/api/v1/iscrizioni-corso/", json=iscrizione_corso_payload(1, 1, 1)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_iscrizione_corso_ok_con_corsi_write_permission(
    client: AsyncClient,
):
    corso = await create_corso(client)
    persona = await create_persona(client)
    stato = await create_stato(client)

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:write"})
    response = await client.post(
        "/api/v1/iscrizioni-corso/",
        json=iscrizione_corso_payload(corso["id"], persona["id"], stato["codice"]),
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_iscrizioni_corso_requires_authentication(client: AsyncClient):
    app.dependency_overrides.pop(get_current_user, None)
    response = await client.get("/api/v1/iscrizioni-corso/")
    assert response.status_code == 401
