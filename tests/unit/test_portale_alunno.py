"""Portale alunno (card #176): viste self-service sola-lettura sulla propria
iscrizione corso — iscrizioni, calendario lezioni, presenze, pagamenti.

Stesso taglio di ``test_schede_alunno.py``: ogni ramo dell'autorizzazione
row-level (proprietario / terzo / non autenticato / senza Persona) ha un
test dedicato, ripetuto sui 3 endpoint scoped a un'iscrizione più
l'endpoint di ingresso (elenco iscrizioni).
"""

from __future__ import annotations

from collections.abc import Collection

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user
from app.models.permesso import Permesso
from app.models.ruolo import Ruolo
from app.models.utente import TipoUtente, Utente
from main import app

BASE = "/api/v1/me"


def _user(
    *,
    superuser: bool = False,
    permessi: Collection[str] = (),
    persona_id: int | None = None,
) -> Utente:
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
        persona_id=persona_id,
    )


# ── Fixture di dominio ────────────────────────────────────────────────────────


async def create_corso(client: AsyncClient, tipo_corso_codice: int = 1, **overrides):
    response = await client.post(
        "/api/v1/tipi-corso/",
        json={"codice": tipo_corso_codice, "descrizione": "Ottoni"},
    )
    assert response.status_code == 201
    payload = {"banda_codice": 1, "tipo_corso_codice": tipo_corso_codice, "anno": 2026}
    payload.update(overrides)
    response = await client.post("/api/v1/corsi/", json=payload)
    assert response.status_code == 201
    return response.json()


async def create_persona(
    client: AsyncClient, nome: str = "Mario", cognome: str = "Rossi"
) -> dict:
    response = await client.post(
        "/api/v1/persone/", json={"banda_codice": 1, "nome": nome, "cognome": cognome}
    )
    assert response.status_code == 201
    return response.json()


async def create_stato(client: AsyncClient, codice: int = 1) -> dict:
    """Idempotente: riusa lo stato se già creato in un ``setup_iscrizione``
    precedente dello stesso test."""
    response = await client.post(
        "/api/v1/stati-iscrizione-corso/",
        json={"codice": codice, "descrizione": "Confermata"},
    )
    if response.status_code == 409:
        get_resp = await client.get(f"/api/v1/stati-iscrizione-corso/{codice}")
        assert get_resp.status_code == 200
        return get_resp.json()
    assert response.status_code == 201
    return response.json()


async def create_iscrizione_corso(
    client: AsyncClient, corso_id: int, persona_id: int, stato_codice: int
) -> dict:
    response = await client.post(
        "/api/v1/iscrizioni-corso/",
        json={
            "corso_id": corso_id,
            "persona_id": persona_id,
            "stato_iscrizione_corso_codice": stato_codice,
            "data_iscrizione": "2026-09-01",
        },
    )
    assert response.status_code == 201
    return response.json()


async def setup_iscrizione(
    client: AsyncClient, nome: str = "Mario", cognome: str = "Rossi", **corso_overrides
) -> tuple[dict, dict]:
    """Crea corso + persona + stato + iscrizione; ritorna (persona, iscrizione)."""
    corso = await create_corso(client, **corso_overrides)
    persona = await create_persona(client, nome, cognome)
    stato = await create_stato(client)
    iscrizione = await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato["codice"]
    )
    return persona, iscrizione


async def create_lezione(
    client: AsyncClient, corso_id: int, data_lezione: str = "2026-10-01T18:00:00"
) -> dict:
    response = await client.post(
        "/api/v1/lezioni/", json={"corso_id": corso_id, "data_lezione": data_lezione}
    )
    assert response.status_code == 201
    return response.json()


async def create_presenza_lezione(
    client: AsyncClient, persona_id: int, lezione_id: int
) -> dict:
    response = await client.post(
        "/api/v1/presenze/", json={"persona_id": persona_id, "lezione_id": lezione_id}
    )
    assert response.status_code == 201
    return response.json()


async def setup_pagamento_env(client: AsyncClient, anno: int = 2026) -> dict:
    """Seed NaturaFlusso + ConfigurazioneBandaAnno con voce corsi impostata,
    prerequisiti dell'auto-posting di ``PagamentoCorso``."""
    await client.post(
        "/api/v1/nature-flusso/", json={"codice": 1, "descrizione": "Banca"}
    )
    cfg_resp = await client.post(
        "/api/v1/configurazioni-banda-anno/", json={"banda_codice": 1, "anno": anno}
    )
    assert cfg_resp.status_code == 201, cfg_resp.text
    cfg = cfg_resp.json()

    voce_resp = await client.post(
        "/api/v1/voci-contabilita/",
        json={
            "banda_codice": 1,
            "voce_contabilita": "Rette corsi",
            "sezione_rendiconto_codice": 2,
            "voce_rendiconto_codice": 2,
            "sottovoce_rendiconto_codice": 8,
        },
    )
    assert voce_resp.status_code == 201, voce_resp.text

    patch_resp = await client.patch(
        f"/api/v1/configurazioni-banda-anno/{cfg['id']}",
        json={"voce_contabilita_corsi_id": voce_resp.json()["id"]},
    )
    assert patch_resp.status_code == 200, patch_resp.text
    return patch_resp.json()


async def create_pagamento(
    client: AsyncClient, iscrizione_corso_id: int, **overrides
) -> dict:
    payload = {
        "iscrizione_corso_id": iscrizione_corso_id,
        "data_pagamento": "2026-02-10",
        "importo": 50.0,
    }
    payload.update(overrides)
    response = await client.post("/api/v1/pagamenti-corso/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _login_come(persona_id: int | None) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=persona_id)


# ── Ingresso: le mie iscrizioni ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_alunno_vede_le_proprie_iscrizioni(client: AsyncClient):
    alunno, iscrizione = await setup_iscrizione(client)
    altro_alunno, _altra = await setup_iscrizione(
        client, "Anna", "Bianchi", tipo_corso_codice=2
    )

    _login_come(alunno["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso")

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["id"] == iscrizione["id"]
    assert data["items"][0]["corso"]["tipo_corso"]["descrizione"] == "Ottoni"
    assert altro_alunno["id"] != alunno["id"]


@pytest.mark.asyncio
async def test_iscrizioni_vuote_se_nessuna_iscrizione(client: AsyncClient):
    persona = await create_persona(client)
    _login_come(persona["id"])

    response = await client.get(f"{BASE}/iscrizioni-corso")
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_iscrizioni_richiede_persona_collegata(client: AsyncClient):
    _login_come(None)
    response = await client.get(f"{BASE}/iscrizioni-corso")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_iscrizioni_richiede_autenticazione(client: AsyncClient):
    app.dependency_overrides.pop(get_current_user, None)
    response = await client.get(f"{BASE}/iscrizioni-corso")
    assert response.status_code == 401


# ── Calendario lezioni ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_alunno_proprietario_vede_calendario(client: AsyncClient):
    alunno, iscrizione = await setup_iscrizione(client)
    await create_lezione(client, iscrizione["corso_id"], "2026-10-01T18:00:00")
    await create_lezione(client, iscrizione["corso_id"], "2026-10-08T18:00:00")

    _login_come(alunno["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso/{iscrizione['id']}/lezioni")

    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2


@pytest.mark.asyncio
async def test_alunno_terzo_non_vede_calendario_altrui(client: AsyncClient):
    _alunno, iscrizione = await setup_iscrizione(client)
    estraneo = await create_persona(client, "Luca", "Neri")

    _login_come(estraneo["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso/{iscrizione['id']}/lezioni")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_calendario_richiede_autenticazione(client: AsyncClient):
    app.dependency_overrides.pop(get_current_user, None)
    response = await client.get(f"{BASE}/iscrizioni-corso/1/lezioni")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_calendario_utente_senza_persona_riceve_403(client: AsyncClient):
    _alunno, iscrizione = await setup_iscrizione(client)
    _login_come(None)
    response = await client.get(f"{BASE}/iscrizioni-corso/{iscrizione['id']}/lezioni")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_calendario_iscrizione_inesistente(client: AsyncClient):
    persona = await create_persona(client)
    _login_come(persona["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso/999/lezioni")
    assert response.status_code == 404


# ── Presenze ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_alunno_proprietario_vede_proprie_presenze(client: AsyncClient):
    alunno, iscrizione = await setup_iscrizione(client)
    lezione = await create_lezione(client, iscrizione["corso_id"])
    await create_presenza_lezione(client, alunno["id"], lezione["id"])

    _login_come(alunno["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso/{iscrizione['id']}/presenze")

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["persona_id"] == alunno["id"]
    assert data["items"][0]["lezione_id"] == lezione["id"]


@pytest.mark.asyncio
async def test_presenze_scoped_al_solo_corso_delliscrizione(client: AsyncClient):
    """Ambiguità Presenza->Corso: la Persona può essere iscritta a più corsi,
    Presenza è legata a persona_id (non a iscrizione_corso_id) — le presenze
    di un ALTRO corso a cui l'alunno è iscritto non devono comparire qui."""
    alunno, iscrizione = await setup_iscrizione(client)
    lezione_corso_proprio = await create_lezione(client, iscrizione["corso_id"])
    await create_presenza_lezione(client, alunno["id"], lezione_corso_proprio["id"])

    altro_corso = await create_corso(client, tipo_corso_codice=2)
    stato = await create_stato(client, codice=2)
    await create_iscrizione_corso(
        client, altro_corso["id"], alunno["id"], stato["codice"]
    )
    lezione_altro_corso = await create_lezione(client, altro_corso["id"])
    await create_presenza_lezione(client, alunno["id"], lezione_altro_corso["id"])

    _login_come(alunno["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso/{iscrizione['id']}/presenze")

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["lezione_id"] == lezione_corso_proprio["id"]


@pytest.mark.asyncio
async def test_alunno_terzo_non_vede_presenze_altrui(client: AsyncClient):
    _alunno, iscrizione = await setup_iscrizione(client)
    estraneo = await create_persona(client, "Luca", "Neri")

    _login_come(estraneo["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso/{iscrizione['id']}/presenze")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_presenze_richiede_autenticazione(client: AsyncClient):
    app.dependency_overrides.pop(get_current_user, None)
    response = await client.get(f"{BASE}/iscrizioni-corso/1/presenze")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_presenze_utente_senza_persona_riceve_403(client: AsyncClient):
    _alunno, iscrizione = await setup_iscrizione(client)
    _login_come(None)
    response = await client.get(f"{BASE}/iscrizioni-corso/{iscrizione['id']}/presenze")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_presenze_iscrizione_inesistente(client: AsyncClient):
    persona = await create_persona(client)
    _login_come(persona["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso/999/presenze")
    assert response.status_code == 404


# ── Pagamenti ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_alunno_proprietario_vede_propri_pagamenti(client: AsyncClient):
    await setup_pagamento_env(client)
    alunno, iscrizione = await setup_iscrizione(client)
    await create_pagamento(client, iscrizione["id"])

    _login_come(alunno["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso/{iscrizione['id']}/pagamenti")

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["iscrizione_corso_id"] == iscrizione["id"]


@pytest.mark.asyncio
async def test_alunno_terzo_non_vede_pagamenti_altrui(client: AsyncClient):
    await setup_pagamento_env(client)
    _alunno, iscrizione = await setup_iscrizione(client)
    await create_pagamento(client, iscrizione["id"])
    estraneo = await create_persona(client, "Luca", "Neri")

    _login_come(estraneo["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso/{iscrizione['id']}/pagamenti")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_pagamenti_richiede_autenticazione(client: AsyncClient):
    app.dependency_overrides.pop(get_current_user, None)
    response = await client.get(f"{BASE}/iscrizioni-corso/1/pagamenti")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_pagamenti_utente_senza_persona_riceve_403(client: AsyncClient):
    _alunno, iscrizione = await setup_iscrizione(client)
    _login_come(None)
    response = await client.get(f"{BASE}/iscrizioni-corso/{iscrizione['id']}/pagamenti")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_pagamenti_iscrizione_inesistente(client: AsyncClient):
    persona = await create_persona(client)
    _login_come(persona["id"])
    response = await client.get(f"{BASE}/iscrizioni-corso/999/pagamenti")
    assert response.status_code == 404
