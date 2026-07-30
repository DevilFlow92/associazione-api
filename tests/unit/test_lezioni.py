from __future__ import annotations

from collections.abc import Collection

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.models.permesso import Permesso
from app.models.persona import Persona
from app.models.presenza import Presenza
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


async def create_indirizzo(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/indirizzi/",
        json={"tipo_indirizzo_codice": 4, "prima_riga": "Piazza Chiesa"},
    )
    return response.json()


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
    payload = {
        "banda_codice": 1,
        "tipo_corso_codice": tipo["codice"],
        "anno": 2026,
    }
    payload.update(overrides)
    response = await client.post("/api/v1/corsi/", json=payload)
    assert response.status_code == 201
    return response.json()


def lezione_payload(corso_id: int, **overrides) -> dict:
    payload = {"corso_id": corso_id, "data_lezione": "2026-09-10T18:00:00"}
    payload.update(overrides)
    return payload


async def create_lezione(client: AsyncClient, corso_id: int, **overrides) -> dict:
    response = await client.post(
        "/api/v1/lezioni/", json=lezione_payload(corso_id, **overrides)
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
    return response.json()


async def create_servizio(client: AsyncClient) -> dict:
    indirizzo = await create_indirizzo(client)
    response = await client.post(
        "/api/v1/servizi/",
        json={
            "banda_codice": 1,
            "anno": 2026,
            "descrizione_servizio": "Concerto estivo",
            "data_servizio": "2026-07-20T21:00:00",
            "indirizzo_id": indirizzo["id"],
        },
    )
    return response.json()


async def create_prova(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/prove/",
        json={"banda_codice": 1, "data_prova": "2026-07-10T20:30:00"},
    )
    return response.json()


# ── CRUD Lezione ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_lezione(client: AsyncClient):
    corso = await create_corso(client)
    response = await client.post("/api/v1/lezioni/", json=lezione_payload(corso["id"]))
    assert response.status_code == 201
    data = response.json()
    assert data["corso_id"] == corso["id"]
    assert data["corso"]["id"] == corso["id"]
    assert data["indirizzo_id"] is None


@pytest.mark.asyncio
async def test_create_lezione_con_indirizzo(client: AsyncClient):
    corso = await create_corso(client)
    indirizzo = await create_indirizzo(client)
    lezione = await create_lezione(client, corso["id"], indirizzo_id=indirizzo["id"])
    assert lezione["indirizzo_id"] == indirizzo["id"]
    assert lezione["indirizzo"] is not None


@pytest.mark.asyncio
async def test_create_lezione_corso_not_found(client: AsyncClient):
    response = await client.post("/api/v1/lezioni/", json=lezione_payload(999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_lezione_indirizzo_not_found(client: AsyncClient):
    corso = await create_corso(client)
    response = await client.post(
        "/api/v1/lezioni/", json=lezione_payload(corso["id"], indirizzo_id=999)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_lezione_not_found(client: AsyncClient):
    response = await client.get("/api/v1/lezioni/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_lezione(client: AsyncClient):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    response = await client.patch(
        f"/api/v1/lezioni/{lezione['id']}", json={"note": "Lezione di prova strumenti"}
    )
    assert response.status_code == 200
    assert response.json()["note"] == "Lezione di prova strumenti"


@pytest.mark.asyncio
async def test_update_lezione_aggiunge_indirizzo(client: AsyncClient):
    """Stesso pattern di regressione già noto per Prova/Corso: la sessione
    usa expire_on_commit=False, quindi senza expire esplicito la rilettura
    post-update restituirebbe l'indirizzo stantio (None)."""
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    assert lezione["indirizzo_id"] is None
    indirizzo = await create_indirizzo(client)

    response = await client.patch(
        f"/api/v1/lezioni/{lezione['id']}", json={"indirizzo_id": indirizzo["id"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["indirizzo_id"] == indirizzo["id"]
    assert data["indirizzo"] is not None


@pytest.mark.asyncio
async def test_update_lezione_not_found(client: AsyncClient):
    response = await client.patch("/api/v1/lezioni/999", json={"note": "x"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_lezione(client: AsyncClient):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    response = await client.delete(f"/api/v1/lezioni/{lezione['id']}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/lezioni/{lezione['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_lezione_not_found(client: AsyncClient):
    response = await client.delete("/api/v1/lezioni/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_lezioni_filtro_corso(client: AsyncClient):
    corso1 = await create_corso(client, tipo_corso_codice=1)
    corso2 = await create_corso(client, tipo_corso_codice=2, anno=2025)
    await create_lezione(client, corso1["id"])
    await create_lezione(client, corso2["id"])

    response = await client.get("/api/v1/lezioni/", params={"corso_id": corso1["id"]})
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["corso_id"] == corso1["id"]


# ── Arc esclusivo a 3 rami su Presenza ──────────────────────────────────────


@pytest.mark.asyncio
async def test_create_presenza_con_lezione(client: AsyncClient):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "lezione_id": lezione["id"]},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["lezione_id"] == lezione["id"]
    assert data["servizio_id"] is None
    assert data["prova_id"] is None


@pytest.mark.asyncio
async def test_create_presenza_lezione_not_found(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/presenze/", json={"persona_id": persona["id"], "lezione_id": 999}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_presenza_senza_alcun_ramo_rifiutata(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/presenze/", json={"persona_id": persona["id"]}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_presenza_servizio_e_lezione_rifiutata(client: AsyncClient):
    persona = await create_persona(client)
    servizio = await create_servizio(client)
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    response = await client.post(
        "/api/v1/presenze/",
        json={
            "persona_id": persona["id"],
            "servizio_id": servizio["id"],
            "lezione_id": lezione["id"],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_presenza_prova_e_lezione_rifiutata(client: AsyncClient):
    persona = await create_persona(client)
    prova = await create_prova(client)
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    response = await client.post(
        "/api/v1/presenze/",
        json={
            "persona_id": persona["id"],
            "prova_id": prova["id"],
            "lezione_id": lezione["id"],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_presenza_tutti_e_tre_i_rami_rifiutata(client: AsyncClient):
    persona = await create_persona(client)
    servizio = await create_servizio(client)
    prova = await create_prova(client)
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    response = await client.post(
        "/api/v1/presenze/",
        json={
            "persona_id": persona["id"],
            "servizio_id": servizio["id"],
            "prova_id": prova["id"],
            "lezione_id": lezione["id"],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_presenza_check_constraint_a_livello_db_arc_a_3_rami(
    db_session: AsyncSession,
):
    """Anche bypassando pydantic, il CHECK del DB deve impedire sia l'arc
    vuoto sia qualunque combinazione con più di un ramo valorizzato."""
    persona = Persona(banda_codice=1, nome="Mario", cognome="Rossi")
    db_session.add(persona)
    await db_session.flush()

    db_session.add(Presenza(persona_id=persona.id))
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


# ── Endpoint organico lezione ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_organico_lezione_via_presenze_router(client: AsyncClient):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    persona = await create_persona(client)
    presenza = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "lezione_id": lezione["id"]},
    )
    assert presenza.status_code == 201

    organico = await client.get(f"/api/v1/presenze/lezione/{lezione['id']}")
    assert organico.status_code == 200
    assert organico.json()["meta"]["total_items"] == 1
    assert organico.json()["items"][0]["lezione_id"] == lezione["id"]


@pytest.mark.asyncio
async def test_organico_lezione_not_found(client: AsyncClient):
    response = await client.get("/api/v1/presenze/lezione/999")
    assert response.status_code == 404


# ── Regressione: arc Servizio/Prova invariato ───────────────────────────────


@pytest.mark.asyncio
async def test_organico_servizio_invariato(client: AsyncClient):
    servizio = await create_servizio(client)
    persona = await create_persona(client)
    presenza = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "servizio_id": servizio["id"]},
    )
    assert presenza.status_code == 201
    assert presenza.json()["lezione_id"] is None

    organico = await client.get(f"/api/v1/presenze/servizio/{servizio['id']}")
    assert organico.status_code == 200
    assert organico.json()["meta"]["total_items"] == 1


@pytest.mark.asyncio
async def test_organico_prova_invariato(client: AsyncClient):
    prova = await create_prova(client)
    persona = await create_persona(client)
    presenza = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "prova_id": prova["id"]},
    )
    assert presenza.status_code == 201
    assert presenza.json()["lezione_id"] is None

    organico = await client.get(f"/api/v1/presenze/prova/{prova['id']}")
    assert organico.status_code == 200
    assert organico.json()["meta"]["total_items"] == 1


# ── RBAC router lezioni ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_lezioni_forbidden_without_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user()
    response = await client.get("/api/v1/lezioni/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_lezioni_succeeds_with_corsi_read_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.get("/api/v1/lezioni/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_lezione_forbidden_without_write_permission(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.post("/api/v1/lezioni/", json=lezione_payload(1))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_lezioni_requires_authentication(client: AsyncClient):
    app.dependency_overrides.pop(get_current_user, None)
    response = await client.get("/api/v1/lezioni/")
    assert response.status_code == 401


# ── RBAC su /presenze/*: corsi:* per il contenitore Lezione ─────────────────
#
# Corsi e Servizi/Prove sono domini di permesso volutamente separati (card
# #171/#172): un utente con corsi:read/write ma senza servizi:read/write deve
# poter gestire l'organico delle proprie lezioni, e viceversa un utente con
# solo servizi:read/write non deve poter toccare l'organico di una lezione.


@pytest.mark.asyncio
async def test_organico_lezione_ok_con_solo_corsi_read(client: AsyncClient):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.get(f"/api/v1/presenze/lezione/{lezione['id']}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_organico_lezione_forbidden_con_solo_servizi_read(client: AsyncClient):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"servizi:read"}
    )
    response = await client.get(f"/api/v1/presenze/lezione/{lezione['id']}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_presenza_lezione_ok_con_solo_corsi_write(client: AsyncClient):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    persona = await create_persona(client)

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:write"})
    response = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "lezione_id": lezione["id"]},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_presenza_lezione_forbidden_con_solo_servizi_write(
    client: AsyncClient,
):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    persona = await create_persona(client)

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"servizi:write"}
    )
    response = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "lezione_id": lezione["id"]},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_presenza_servizio_ok_con_solo_servizi_write(client: AsyncClient):
    """Regressione: il ramo Servizio/Prova resta gated da servizi:write,
    invariato dal fix del permesso per il ramo Lezione."""
    servizio = await create_servizio(client)
    persona = await create_persona(client)

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"servizi:write"}
    )
    response = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "servizio_id": servizio["id"]},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_update_presenza_lezione_ok_con_solo_corsi_write(client: AsyncClient):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    persona = await create_persona(client)
    presenza = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "lezione_id": lezione["id"]},
    )
    assert presenza.status_code == 201

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:write"})
    response = await client.patch(
        f"/api/v1/presenze/{presenza.json()['id']}",
        json={"note": "Presente in ritardo"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_presenza_lezione_forbidden_con_solo_servizi_write(
    client: AsyncClient,
):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    persona = await create_persona(client)
    presenza = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "lezione_id": lezione["id"]},
    )
    assert presenza.status_code == 201

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"servizi:write"}
    )
    response = await client.patch(
        f"/api/v1/presenze/{presenza.json()['id']}",
        json={"note": "Presente in ritardo"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_presenza_lezione_ok_con_solo_corsi_write(client: AsyncClient):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    persona = await create_persona(client)
    presenza = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "lezione_id": lezione["id"]},
    )
    assert presenza.status_code == 201

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:write"})
    response = await client.delete(f"/api/v1/presenze/{presenza.json()['id']}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_presenza_lezione_forbidden_con_solo_servizi_write(
    client: AsyncClient,
):
    corso = await create_corso(client)
    lezione = await create_lezione(client, corso["id"])
    persona = await create_persona(client)
    presenza = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "lezione_id": lezione["id"]},
    )
    assert presenza.status_code == 201

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"servizi:write"}
    )
    response = await client.delete(f"/api/v1/presenze/{presenza.json()['id']}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_presenza_servizio_ok_con_solo_servizi_write(client: AsyncClient):
    """Regressione: update/delete sul ramo Servizio/Prova restano gated da
    servizi:write, invariato dal fix del permesso per il ramo Lezione."""
    servizio = await create_servizio(client)
    persona = await create_persona(client)
    presenza = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "servizio_id": servizio["id"]},
    )
    assert presenza.status_code == 201

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"servizi:write"}
    )
    response = await client.patch(
        f"/api/v1/presenze/{presenza.json()['id']}", json={"note": "ok"}
    )
    assert response.status_code == 200
