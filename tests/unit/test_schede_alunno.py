"""Scheda alunno: CRUD del personale corsi + il primo controllo row-level.

La parte critica di questo modulo è la sezione "Autorizzazione row-level":
ogni ramo della decisione (gestione / alunno proprietario / alunno terzo /
utente senza Persona collegata / non autenticato) ha un test dedicato e
nominato, sia sulle funzioni pure di ``rbac_row_level`` sia end-to-end sugli
endpoint.
"""

from __future__ import annotations

from collections.abc import Collection

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.storage import storage
from app.exceptions.scheda_alunno import AccessoSchedaAlunnoNegatoError
from app.models.corso import Corso
from app.models.permesso import Permesso
from app.models.ruolo import Ruolo
from app.models.scheda_alunno_materiale import SchedaAlunnoMateriale
from app.models.scheda_alunno_voce_storico import SchedaAlunnoVoceStorico
from app.models.utente import TipoUtente, Utente
from app.services.rbac_row_level import (
    LivelloAccessoScheda,
    assert_puo_leggere_scheda,
    assert_puo_scrivere_autovalutazione,
    assert_puo_scrivere_scheda,
    e_docente_del_corso,
    livello_accesso_scheda,
)
from main import app


def _corso(
    *,
    insegnante_persona_id: int | None = None,
    coordinatore_persona_id: int | None = None,
) -> Corso:
    return Corso(
        id=1,
        banda_codice=1,
        tipo_corso_codice=1,
        anno=2026,
        insegnante_persona_id=insegnante_persona_id,
        coordinatore_persona_id=coordinatore_persona_id,
    )


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


# ── Fixture di dominio (create dal client superuser di default) ──────────────


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
    response = await client.post(
        "/api/v1/stati-iscrizione-corso/",
        json={"codice": codice, "descrizione": "Confermata"},
    )
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
    """Crea corso + persona + stato + iscrizione; ritorna (persona, iscrizione).

    ``**corso_overrides`` passa a ``create_corso`` (es.
    ``insegnante_persona_id=...``/``coordinatore_persona_id=...``), per i
    test che devono legare l'alunno a un corso con un docente specifico.
    """
    corso = await create_corso(client, **corso_overrides)
    persona = await create_persona(client, nome, cognome)
    stato = await create_stato(client)
    iscrizione = await create_iscrizione_corso(
        client, corso["id"], persona["id"], stato["codice"]
    )
    return persona, iscrizione


async def create_scheda(
    client: AsyncClient, iscrizione_corso_id: int, **overrides
) -> dict:
    payload = {"iscrizione_corso_id": iscrizione_corso_id}
    payload.update(overrides)
    response = await client.post("/api/v1/schede-alunno/", json=payload)
    assert response.status_code == 201
    return response.json()


async def create_categoria_voce(
    client: AsyncClient, codice: int = 1, descrizione: str = "Scale"
) -> dict:
    response = await client.post(
        "/api/v1/categorie-voce-programma/",
        json={"codice": codice, "descrizione": descrizione},
    )
    assert response.status_code == 201
    return response.json()


async def create_voce_catalogo(
    client: AsyncClient,
    tipo_corso_codice: int,
    categoria_codice: int = 1,
    **overrides,
) -> dict:
    payload = {
        "tipo_corso_codice": tipo_corso_codice,
        "categoria_codice": categoria_codice,
        "testo": "Scala di Do maggiore",
    }
    payload.update(overrides)
    response = await client.post("/api/v1/catalogo-programmi/", json=payload)
    assert response.status_code == 201
    return response.json()


async def create_voce_scheda(
    client: AsyncClient,
    scheda_id: int,
    voce_catalogo_id: int,
    stato: str = "da_iniziare",
    **overrides,
) -> dict:
    payload = {"voce_catalogo_id": voce_catalogo_id, "stato": stato, "ordine": 1}
    payload.update(overrides)
    response = await client.post(
        f"/api/v1/schede-alunno/{scheda_id}/voci", json=payload
    )
    assert response.status_code == 201
    return response.json()


async def upload_materiale_file(
    client: AsyncClient,
    scheda_id: int,
    titolo: str = "Spartito di studio",
    filename: str = "spartito.pdf",
    content: bytes = b"contenuto del materiale di prova",
    content_type: str = "application/pdf",
):
    return await client.post(
        f"/api/v1/schede-alunno/{scheda_id}/materiali/file",
        data={"titolo": titolo},
        files={"file": (filename, content, content_type)},
    )


async def create_materiale_file(client: AsyncClient, scheda_id: int, **kwargs) -> dict:
    response = await upload_materiale_file(client, scheda_id, **kwargs)
    assert response.status_code == 201
    return response.json()


async def create_materiale_link(
    client: AsyncClient,
    scheda_id: int,
    titolo: str = "Registrazione su YouTube",
    url: str = "https://youtube.com/watch?v=abc123",
) -> dict:
    response = await client.post(
        f"/api/v1/schede-alunno/{scheda_id}/materiali/link",
        json={"titolo": titolo, "url": url},
    )
    assert response.status_code == 201
    return response.json()


# ── CRUD ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_scheda_alunno(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)

    response = await client.post(
        "/api/v1/schede-alunno/",
        json={
            "iscrizione_corso_id": iscrizione["id"],
            "note": "Rivedere l'imboccatura",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["iscrizione_corso_id"] == iscrizione["id"]
    assert data["note"] == "Rivedere l'imboccatura"
    assert data["voci"] == []
    assert data["iscrizione_corso"]["persona_id"] == _persona["id"]


@pytest.mark.asyncio
async def test_create_scheda_alunno_iscrizione_not_found(client: AsyncClient):
    response = await client.post(
        "/api/v1/schede-alunno/",
        json={"iscrizione_corso_id": 999},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_scheda_alunno_duplicata(client: AsyncClient):
    """Una sola scheda per iscrizione (vincolo UNIQUE)."""
    _persona, iscrizione = await setup_iscrizione(client)
    await create_scheda(client, iscrizione["id"])

    response = await client.post(
        "/api/v1/schede-alunno/",
        json={"iscrizione_corso_id": iscrizione["id"]},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_scheda_alunno_not_found(client: AsyncClient):
    response = await client.get("/api/v1/schede-alunno/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_scheda_alunno(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    response = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}",
        json={"note": "Aggiornato dopo la lezione"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["note"] == "Aggiornato dopo la lezione"


@pytest.mark.asyncio
async def test_update_scheda_alunno_not_found(client: AsyncClient):
    response = await client.patch("/api/v1/schede-alunno/999", json={"note": "x"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_scheda_alunno(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    response = await client.delete(f"/api/v1/schede-alunno/{scheda['id']}")
    assert response.status_code == 204

    riletta = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    assert riletta.status_code == 404


@pytest.mark.asyncio
async def test_delete_scheda_alunno_not_found(client: AsyncClient):
    response = await client.delete("/api/v1/schede-alunno/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_schede_alunno_filtro_iscrizione(client: AsyncClient):
    corso = await create_corso(client)
    stato = await create_stato(client)
    persona1 = await create_persona(client, "Mario", "Rossi")
    persona2 = await create_persona(client, "Anna", "Bianchi")
    iscr1 = await create_iscrizione_corso(
        client, corso["id"], persona1["id"], stato["codice"]
    )
    iscr2 = await create_iscrizione_corso(
        client, corso["id"], persona2["id"], stato["codice"]
    )
    await create_scheda(client, iscr1["id"])
    await create_scheda(client, iscr2["id"])

    response = await client.get("/api/v1/schede-alunno/")
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 2

    response = await client.get(
        "/api/v1/schede-alunno/", params={"iscrizione_corso_id": iscr1["id"]}
    )
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 1


@pytest.mark.asyncio
async def test_audit_aggiornato_da_deriva_dall_utente_autenticato(client: AsyncClient):
    """``aggiornato_da_persona_id`` viene dal principal, non dal payload."""
    insegnante = await create_persona(client, "Giulia", "Verdi")
    _alunno, iscrizione = await setup_iscrizione(
        client, insegnante_persona_id=insegnante["id"]
    )

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:write"}, persona_id=insegnante["id"]
    )
    response = await client.post(
        "/api/v1/schede-alunno/",
        json={
            "iscrizione_corso_id": iscrizione["id"],
            # Tentativo di falsificare l'audit: il campo non è nello schema
            # di input, quindi viene semplicemente ignorato.
            "aggiornato_da_persona_id": 999,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["aggiornato_da_persona_id"] == insegnante["id"]
    assert data["aggiornato_da"]["cognome"] == "Verdi"


# ── Autorizzazione row-level: funzioni pure ──────────────────────────────────


def test_livello_accesso_completo_con_corsi_write():
    utente = _user(permessi={"corsi:write"}, persona_id=7)
    assert livello_accesso_scheda(utente, 42) is LivelloAccessoScheda.COMPLETO


def test_livello_accesso_completo_per_superuser():
    assert livello_accesso_scheda(_user(superuser=True), 42) is (
        LivelloAccessoScheda.COMPLETO
    )


def test_livello_accesso_sola_lettura_per_alunno_proprietario():
    utente = _user(persona_id=42)
    assert livello_accesso_scheda(utente, 42) is LivelloAccessoScheda.SOLA_LETTURA


def test_livello_accesso_nessuno_per_alunno_terzo():
    utente = _user(persona_id=7)
    assert livello_accesso_scheda(utente, 42) is LivelloAccessoScheda.NESSUNO


def test_livello_accesso_nessuno_per_utente_senza_persona_collegata():
    """``persona_id`` nullo non deve mai combaciare con l'alunno."""
    utente = _user(persona_id=None)
    assert livello_accesso_scheda(utente, 42) is LivelloAccessoScheda.NESSUNO


def test_livello_accesso_nessuno_se_entrambi_i_persona_id_sono_nulli():
    """Il caso che rende non vacuo il controllo ``is not None``.

    Oggi ``iscrizioni_corso.persona_id`` è NOT NULL, quindi il confronto
    ``None == <int>`` basterebbe a negare. Questo test fissa il comportamento
    se quel vincolo cambiasse: due valori nulli non sono un'identità, e senza
    il controllo esplicito ``None == None`` concederebbe la lettura a
    qualunque utente senza Persona collegata."""
    utente = _user(persona_id=None)
    assert livello_accesso_scheda(utente, None) is (  # type: ignore[arg-type]
        LivelloAccessoScheda.NESSUNO
    )


def test_assert_puo_leggere_consente_alunno_proprietario():
    assert_puo_leggere_scheda(_user(persona_id=42), 42)


def test_assert_puo_leggere_nega_alunno_terzo():
    with pytest.raises(AccessoSchedaAlunnoNegatoError):
        assert_puo_leggere_scheda(_user(persona_id=7), 42)


def test_assert_puo_scrivere_nega_alunno_proprietario():
    """Il proprietario legge la propria scheda ma non la scrive, a prescindere
    dal corso: non ha mai ``corsi:write``."""
    with pytest.raises(AccessoSchedaAlunnoNegatoError):
        assert_puo_scrivere_scheda(_user(persona_id=42), _corso())


def test_assert_puo_scrivere_consente_insegnante_del_corso():
    utente = _user(permessi={"corsi:write"}, persona_id=10)
    assert_puo_scrivere_scheda(utente, _corso(insegnante_persona_id=10))


def test_assert_puo_scrivere_consente_coordinatore_del_corso():
    utente = _user(permessi={"corsi:write"}, persona_id=20)
    assert_puo_scrivere_scheda(utente, _corso(coordinatore_persona_id=20))


def test_assert_puo_scrivere_nega_corsi_write_da_solo_senza_essere_docente():
    """Il cuore della restrizione di questa card: ``corsi:write`` non basta
    più, serve essere insegnante/coordinatore di QUESTO corso."""
    utente = _user(permessi={"corsi:write"}, persona_id=99)
    with pytest.raises(AccessoSchedaAlunnoNegatoError):
        assert_puo_scrivere_scheda(utente, _corso(insegnante_persona_id=10))


def test_assert_puo_scrivere_consente_superuser_senza_essere_docente():
    """Il superuser bypassa la restrizione per-corso, stesso pattern di
    ``permessi_archivio.require_write``."""
    utente = _user(superuser=True, persona_id=99)
    assert_puo_scrivere_scheda(utente, _corso(insegnante_persona_id=10))


def test_e_docente_del_corso_true_per_insegnante():
    utente = _user(persona_id=10)
    assert e_docente_del_corso(utente, _corso(insegnante_persona_id=10)) is True


def test_e_docente_del_corso_true_per_coordinatore():
    utente = _user(persona_id=20)
    assert e_docente_del_corso(utente, _corso(coordinatore_persona_id=20)) is True


def test_e_docente_del_corso_false_per_terzo():
    utente = _user(persona_id=99)
    corso = _corso(insegnante_persona_id=10, coordinatore_persona_id=20)
    assert e_docente_del_corso(utente, corso) is False


def test_e_docente_del_corso_false_per_utente_senza_persona_collegata():
    """Stesso guardrail di ``e_alunno_della_scheda``: ``None`` non deve mai
    combaciare con ``None`` (corso senza insegnante né coordinatore)."""
    utente = _user(persona_id=None)
    assert e_docente_del_corso(utente, _corso()) is False


# ── Autorizzazione row-level: perimetro per-corso della scrittura ───────────
# (restrizione introdotta dopo la card #175: corsi:write da solo non basta
# più per SCRIVERE, serve essere insegnante/coordinatore di QUESTO corso; la
# lettura resta invece ampia, invariata rispetto alla card originale)


@pytest.mark.asyncio
async def test_insegnante_del_corso_legge_e_scrive_la_scheda(client: AsyncClient):
    """Ramo 1 — chi ha ``corsi:write`` ED è insegnante/coordinatore di QUESTO
    corso legge e scrive la scheda dei propri alunni."""
    insegnante = await create_persona(client, "Giulia", "Verdi")
    _alunno, iscrizione = await setup_iscrizione(
        client, insegnante_persona_id=insegnante["id"]
    )
    scheda = await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:read", "corsi:write"}, persona_id=insegnante["id"]
    )

    lettura = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    assert lettura.status_code == 200

    scrittura = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}", json={"note": "Studio n.7"}
    )
    assert scrittura.status_code == 200
    assert scrittura.json()["note"] == "Studio n.7"

    propria = await client.get(f"/api/v1/schede-alunno/me/{iscrizione['id']}")
    assert propria.status_code == 200


@pytest.mark.asyncio
async def test_coordinatore_del_corso_scrive_la_scheda(client: AsyncClient):
    """Il coordinatore ha lo stesso diritto di scrittura dell'insegnante."""
    coordinatore = await create_persona(client, "Luigi", "Bruni")
    _alunno, iscrizione = await setup_iscrizione(
        client, coordinatore_persona_id=coordinatore["id"]
    )
    scheda = await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:write"}, persona_id=coordinatore["id"]
    )
    response = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}", json={"note": "Scale minori"}
    )
    assert response.status_code == 200
    assert response.json()["note"] == "Scale minori"


@pytest.mark.asyncio
async def test_insegnante_di_altro_corso_non_scrive_scheda(client: AsyncClient):
    """Il caso che questa restrizione esiste per impedire: ``corsi:write`` da
    solo non basta più, l'insegnante di un ALTRO corso non tocca schede che
    non sono le sue."""
    insegnante_altro_corso = await create_persona(client, "Marco", "Neri")
    await create_corso(
        client,
        tipo_corso_codice=2,
        insegnante_persona_id=insegnante_altro_corso["id"],
    )
    _alunno, iscrizione = await setup_iscrizione(client)  # corso senza docenti
    scheda = await create_scheda(client, iscrizione["id"], note="Originale")

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:read", "corsi:write"}, persona_id=insegnante_altro_corso["id"]
    )

    patch = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}", json={"note": "Alterato"}
    )
    assert patch.status_code == 403

    # L'autorizzazione è valutata prima del controllo di duplicato (stesso
    # ordine "authz prima di tutto" già in uso per la lettura): 403, non 409.
    post = await client.post(
        "/api/v1/schede-alunno/",
        json={"iscrizione_corso_id": iscrizione["id"]},
    )
    assert post.status_code == 403

    delete = await client.delete(f"/api/v1/schede-alunno/{scheda['id']}")
    assert delete.status_code == 403


@pytest.mark.asyncio
async def test_insegnante_di_altro_corso_legge_comunque_qualsiasi_scheda(
    client: AsyncClient,
):
    """La LETTURA resta ampia (non ristretta da questa card): un insegnante
    con ``corsi:read`` legge la scheda anche di un corso che non è il suo —
    solo la scrittura è ora vincolata al corso specifico."""
    insegnante_altro_corso = await create_persona(client, "Marco", "Neri")
    await create_corso(
        client,
        tipo_corso_codice=2,
        insegnante_persona_id=insegnante_altro_corso["id"],
    )
    _alunno, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:read"}, persona_id=insegnante_altro_corso["id"]
    )
    response = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_superuser_scrive_scheda_senza_essere_docente_del_corso(
    client: AsyncClient,
):
    """Il superuser bypassa la restrizione per-corso, stesso pattern già in
    uso per ``permessi_archivio.require_write``."""
    insegnante = await create_persona(client, "Giulia", "Verdi")
    _alunno, iscrizione = await setup_iscrizione(
        client, insegnante_persona_id=insegnante["id"]
    )
    scheda = await create_scheda(client, iscrizione["id"])

    # persona_id diverso dall'insegnante del corso: il superuser non è né
    # insegnante né coordinatore di questo corso, eppure scrive comunque.
    estraneo_al_corso = await create_persona(client, "Anna", "Bianchi")
    app.dependency_overrides[get_current_user] = lambda: _user(
        superuser=True, persona_id=estraneo_al_corso["id"]
    )
    response = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}", json={"note": "Studio n.9"}
    )
    assert response.status_code == 200
    assert response.json()["note"] == "Studio n.9"


# ── Autorizzazione row-level: i 6 rami end-to-end (card #175 originale) ─────


@pytest.mark.asyncio
async def test_alunno_proprietario_legge_la_propria_scheda(client: AsyncClient):
    """Ramo 2 — l'alunno non ha alcun permesso ``corsi:*`` e legge comunque
    la propria scheda: è esattamente ciò che il row-level esiste per fare."""
    alunno, iscrizione = await setup_iscrizione(client)
    await create_scheda(client, iscrizione["id"], note="Scale maggiori")

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])
    response = await client.get(f"/api/v1/schede-alunno/me/{iscrizione['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["note"] == "Scale maggiori"
    assert data["iscrizione_corso"]["persona_id"] == alunno["id"]


@pytest.mark.asyncio
async def test_alunno_proprietario_non_scrive_la_propria_scheda(client: AsyncClient):
    """Ramo 3 — sola lettura: la scheda la redige insegnante/coordinatore."""
    alunno, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])

    patch = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}",
        json={"note": "mi assegno io il programma"},
    )
    assert patch.status_code == 403

    post = await client.post(
        "/api/v1/schede-alunno/",
        json={"iscrizione_corso_id": iscrizione["id"]},
    )
    assert post.status_code == 403

    delete = await client.delete(f"/api/v1/schede-alunno/{scheda['id']}")
    assert delete.status_code == 403


@pytest.mark.asyncio
async def test_alunno_terzo_non_legge_scheda_altrui(client: AsyncClient):
    """Ramo 4 — il caso che questa card esiste per impedire."""
    corso = await create_corso(client)
    stato = await create_stato(client)
    alunno = await create_persona(client, "Mario", "Rossi")
    altro_alunno = await create_persona(client, "Anna", "Bianchi")
    iscrizione = await create_iscrizione_corso(
        client, corso["id"], alunno["id"], stato["codice"]
    )
    await create_scheda(client, iscrizione["id"], note="Riservato a Mario")

    app.dependency_overrides[get_current_user] = lambda: _user(
        persona_id=altro_alunno["id"]
    )
    response = await client.get(f"/api/v1/schede-alunno/me/{iscrizione['id']}")

    assert response.status_code == 403
    assert "Riservato a Mario" not in response.text


@pytest.mark.asyncio
async def test_utente_senza_persona_collegata_non_legge_scheda(client: AsyncClient):
    """Ramo 5 — ``utente.persona_id`` nullo: nessuna corrispondenza possibile,
    nemmeno per confronto ``None == None``."""
    _alunno, iscrizione = await setup_iscrizione(client)
    await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=None)
    response = await client.get(f"/api/v1/schede-alunno/me/{iscrizione['id']}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_scheda_alunno_richiede_autenticazione(client: AsyncClient):
    """Ramo 6 — nessuna credenziale: 401 su entrambe le superfici."""
    app.dependency_overrides.pop(get_current_user, None)

    assert (await client.get("/api/v1/schede-alunno/me/1")).status_code == 401
    assert (await client.get("/api/v1/schede-alunno/")).status_code == 401
    assert (
        await client.post("/api/v1/schede-alunno/", json={"iscrizione_corso_id": 1})
    ).status_code == 401


# ── Contorni del row-level ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_alunno_terzo_riceve_403_anche_se_la_scheda_non_esiste(
    client: AsyncClient,
):
    """L'autorizzazione è valutata prima di cercare la scheda: un non
    autorizzato non deve poter distinguere "assente" da "presente ma non tua"."""
    _alunno, iscrizione = await setup_iscrizione(client)
    estraneo = await create_persona(client, "Luca", "Neri")

    app.dependency_overrides[get_current_user] = lambda: _user(
        persona_id=estraneo["id"]
    )
    response = await client.get(f"/api/v1/schede-alunno/me/{iscrizione['id']}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_alunno_proprietario_senza_scheda_riceve_404(client: AsyncClient):
    """Il proprietario è autorizzato: se la scheda non è ancora stata scritta
    riceve 404, non 403."""
    alunno, iscrizione = await setup_iscrizione(client)

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])
    response = await client.get(f"/api/v1/schede-alunno/me/{iscrizione['id']}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_me_scheda_alunno_iscrizione_inesistente(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=1)
    response = await client.get("/api/v1/schede-alunno/me/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_schede_alunno_forbidden_senza_corsi_read(client: AsyncClient):
    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=1)
    response = await client.get("/api/v1/schede-alunno/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_scheda_alunno_ok_con_corsi_read(client: AsyncClient):
    _alunno, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(permessi={"corsi:read"})
    response = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    assert response.status_code == 200


# ── Voci di programma: CRUD ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_voce_scheda_alunno(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])

    response = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/voci",
        json={
            "voce_catalogo_id": voce_catalogo["id"],
            "stato": "da_iniziare",
            "dettaglio": "battute 1-16",
            "ordine": 1,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["scheda_alunno_id"] == scheda["id"]
    assert data["stato"] == "da_iniziare"
    assert data["dettaglio"] == "battute 1-16"
    assert data["ordine"] == 1
    assert data["voce_catalogo"]["id"] == voce_catalogo["id"]
    assert data["voce_catalogo"]["testo"] == voce_catalogo["testo"]


@pytest.mark.asyncio
async def test_create_voce_scheda_alunno_scrive_il_valore_enum_non_il_nome(
    client: AsyncClient, db_session: AsyncSession
):
    """Regression per il bug #226: senza ``values_callable``, SQLAlchemy
    scrive sulla colonna il NOME del membro enum Python (``DA_INIZIARE``)
    invece del suo VALORE (``da_iniziare``). Su Postgres questo fallisce con
    ``InvalidTextRepresentationError`` perché il tipo ``stato_voce_programma``
    accetta solo i valori minuscoli — ma il bind e il result processor di
    SQLAlchemy usano la stessa mappatura (rotta) in scrittura e in lettura,
    quindi leggere lo ``stato`` tramite l'ORM (o tramite la response API,
    validata da Pydantic) fa tornare comunque ``StatoVoceProgramma.DA_INIZIARE``
    e nasconde il bug. Per questo qui leggiamo la stringa grezza con SQL
    testuale, bypassando il result processor dell'ORM. Anche SQLite non
    avrebbe intercettato la regressione da solo (nessun CHECK constraint reale
    sui valori enum in questo progetto), quindi questo test resta l'unico
    modo per accorgersene su qualunque backend.
    """
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])

    response = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/voci",
        json={
            "voce_catalogo_id": voce_catalogo["id"],
            "stato": "da_iniziare",
            "ordine": 1,
        },
    )
    assert response.status_code == 201
    voce_id = response.json()["id"]

    raw = await db_session.execute(
        text("SELECT stato FROM scheda_alunno_voci WHERE id = :id"),
        {"id": voce_id},
    )
    assert raw.scalar_one() == "da_iniziare"


@pytest.mark.asyncio
async def test_create_voce_scheda_alunno_scheda_not_found(client: AsyncClient):
    corso = await create_corso(client)
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(
        client, corso["tipo_corso_codice"], categoria["codice"]
    )

    response = await client.post(
        "/api/v1/schede-alunno/999/voci",
        json={
            "voce_catalogo_id": voce_catalogo["id"],
            "stato": "da_iniziare",
            "ordine": 1,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_voce_scheda_alunno_catalogo_inesistente(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    response = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/voci",
        json={"voce_catalogo_id": 999, "stato": "da_iniziare", "ordine": 1},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_voce_scheda_alunno(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])
    voce = await create_voce_scheda(client, scheda["id"], voce_catalogo["id"])

    response = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}/voci/{voce['id']}",
        json={"stato": "in_corso", "dettaglio": "quasi pronto", "ordine": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stato"] == "in_corso"
    assert data["dettaglio"] == "quasi pronto"
    assert data["ordine"] == 2


@pytest.mark.asyncio
async def test_delete_voce_scheda_alunno(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])
    voce = await create_voce_scheda(client, scheda["id"], voce_catalogo["id"])

    response = await client.delete(
        f"/api/v1/schede-alunno/{scheda['id']}/voci/{voce['id']}"
    )
    assert response.status_code == 204

    riletta = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    assert riletta.json()["voci"] == []


@pytest.mark.asyncio
async def test_update_delete_voce_scheda_alunno_not_found(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    patch = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}/voci/999", json={"stato": "in_corso"}
    )
    assert patch.status_code == 404

    delete = await client.delete(f"/api/v1/schede-alunno/{scheda['id']}/voci/999")
    assert delete.status_code == 404


@pytest.mark.asyncio
async def test_voce_di_altra_scheda_non_raggiungibile(client: AsyncClient):
    """L'endpoint è annidato sotto la scheda: una voce esistente ma di
    un'ALTRA scheda non è raggiungibile da qui (404, non un 200 su dati
    altrui)."""
    corso = await create_corso(client)
    stato = await create_stato(client)
    persona1 = await create_persona(client, "Mario", "Rossi")
    persona2 = await create_persona(client, "Anna", "Bianchi")
    iscr1 = await create_iscrizione_corso(
        client, corso["id"], persona1["id"], stato["codice"]
    )
    iscr2 = await create_iscrizione_corso(
        client, corso["id"], persona2["id"], stato["codice"]
    )
    scheda1 = await create_scheda(client, iscr1["id"])
    scheda2 = await create_scheda(client, iscr2["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(
        client, corso["tipo_corso_codice"], categoria["codice"]
    )
    voce = await create_voce_scheda(client, scheda1["id"], voce_catalogo["id"])

    response = await client.patch(
        f"/api/v1/schede-alunno/{scheda2['id']}/voci/{voce['id']}",
        json={"stato": "in_corso"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_voci_scheda_alunno_ordinate_per_ordine(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    codice = categoria["codice"]
    v1 = await create_voce_catalogo(client, 1, codice, testo="Scala di Do")
    v2 = await create_voce_catalogo(client, 1, codice, testo="Scala di Sol")
    v3 = await create_voce_catalogo(client, 1, codice, testo="Scala di Re")

    await create_voce_scheda(client, scheda["id"], v1["id"], ordine=3)
    await create_voce_scheda(client, scheda["id"], v2["id"], ordine=1)
    await create_voce_scheda(client, scheda["id"], v3["id"], ordine=2)

    response = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    assert response.status_code == 200
    voci = response.json()["voci"]
    assert [v["ordine"] for v in voci] == [1, 2, 3]
    assert [v["voce_catalogo"]["testo"] for v in voci] == [
        "Scala di Sol",
        "Scala di Re",
        "Scala di Do",
    ]


@pytest.mark.asyncio
async def test_stessa_voce_catalogo_due_volte_dettaglio_diverso_ammesso(
    client: AsyncClient,
):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(
        client, 1, categoria["codice"], testo="Studio n.9"
    )

    v1 = await create_voce_scheda(
        client, scheda["id"], voce_catalogo["id"], dettaglio="battute 1-16", ordine=1
    )
    v2 = await create_voce_scheda(
        client, scheda["id"], voce_catalogo["id"], dettaglio="battute 17-32", ordine=2
    )
    assert v1["id"] != v2["id"]

    response = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    voci = response.json()["voci"]
    assert len(voci) == 2
    assert {v["dettaglio"] for v in voci} == {"battute 1-16", "battute 17-32"}


@pytest.mark.asyncio
async def test_voce_catalogo_disattivata_rifiutata(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])

    disattiva = await client.patch(
        f"/api/v1/catalogo-programmi/{voce_catalogo['id']}", json={"attiva": False}
    )
    assert disattiva.status_code == 200

    response = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/voci",
        json={
            "voce_catalogo_id": voce_catalogo["id"],
            "stato": "da_iniziare",
            "ordine": 1,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_voce_catalogo_tipo_corso_diverso_rifiutata(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)  # corso tipo_corso_codice=1
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    altro_tipo = await client.post(
        "/api/v1/tipi-corso/", json={"codice": 2, "descrizione": "Legni"}
    )
    assert altro_tipo.status_code == 201
    voce_catalogo = await create_voce_catalogo(client, 2, categoria["codice"])

    response = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/voci",
        json={
            "voce_catalogo_id": voce_catalogo["id"],
            "stato": "da_iniziare",
            "ordine": 1,
        },
    )
    assert response.status_code == 422


# ── Voci di programma: autorizzazione row-level ──────────────────────────────


@pytest.mark.asyncio
async def test_insegnante_di_altro_corso_non_scrive_voci(client: AsyncClient):
    insegnante_altro_corso = await create_persona(client, "Marco", "Neri")
    await create_corso(
        client,
        tipo_corso_codice=2,
        insegnante_persona_id=insegnante_altro_corso["id"],
    )
    _alunno, iscrizione = await setup_iscrizione(client)  # corso senza docenti
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])
    voce = await create_voce_scheda(client, scheda["id"], voce_catalogo["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:read", "corsi:write"}, persona_id=insegnante_altro_corso["id"]
    )

    post = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/voci",
        json={
            "voce_catalogo_id": voce_catalogo["id"],
            "stato": "da_iniziare",
            "ordine": 2,
        },
    )
    assert post.status_code == 403

    patch = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}/voci/{voce['id']}",
        json={"stato": "in_corso"},
    )
    assert patch.status_code == 403

    delete = await client.delete(
        f"/api/v1/schede-alunno/{scheda['id']}/voci/{voce['id']}"
    )
    assert delete.status_code == 403


@pytest.mark.asyncio
async def test_alunno_proprietario_legge_voci_non_le_scrive(client: AsyncClient):
    alunno, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])
    voce = await create_voce_scheda(client, scheda["id"], voce_catalogo["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])

    lettura = await client.get(f"/api/v1/schede-alunno/me/{iscrizione['id']}")
    assert lettura.status_code == 200
    assert len(lettura.json()["voci"]) == 1

    post = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/voci",
        json={
            "voce_catalogo_id": voce_catalogo["id"],
            "stato": "da_iniziare",
            "ordine": 2,
        },
    )
    assert post.status_code == 403

    patch = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}/voci/{voce['id']}",
        json={"stato": "in_corso"},
    )
    assert patch.status_code == 403

    delete = await client.delete(
        f"/api/v1/schede-alunno/{scheda['id']}/voci/{voce['id']}"
    )
    assert delete.status_code == 403


# ── Storico dei cambi di stato ───────────────────────────────────────────────


async def get_storico(
    db_session: AsyncSession, scheda_alunno_id: int
) -> list[SchedaAlunnoVoceStorico]:
    stmt = (
        select(SchedaAlunnoVoceStorico)
        .where(SchedaAlunnoVoceStorico.scheda_alunno_id == scheda_alunno_id)
        .order_by(SchedaAlunnoVoceStorico.id)
    )
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_storico_riga_creata_alla_creazione_della_voce(
    client: AsyncClient, db_session: AsyncSession
):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])
    voce = await create_voce_scheda(
        client, scheda["id"], voce_catalogo["id"], stato="in_corso"
    )

    righe = await get_storico(db_session, scheda["id"])
    assert len(righe) == 1
    assert righe[0].scheda_alunno_voce_id == voce["id"]
    assert righe[0].voce_catalogo_id == voce_catalogo["id"]
    assert righe[0].stato_precedente is None
    assert righe[0].stato_nuovo == "in_corso"


@pytest.mark.asyncio
async def test_storico_riga_creata_al_cambio_di_stato(
    client: AsyncClient, db_session: AsyncSession
):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])
    voce = await create_voce_scheda(
        client, scheda["id"], voce_catalogo["id"], stato="da_iniziare"
    )

    response = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}/voci/{voce['id']}",
        json={"stato": "in_corso"},
    )
    assert response.status_code == 200

    righe = await get_storico(db_session, scheda["id"])
    assert len(righe) == 2
    assert righe[-1].stato_precedente == "da_iniziare"
    assert righe[-1].stato_nuovo == "in_corso"


@pytest.mark.asyncio
async def test_storico_nessuna_riga_se_il_patch_non_cambia_lo_stato(
    client: AsyncClient, db_session: AsyncSession
):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])
    voce = await create_voce_scheda(
        client, scheda["id"], voce_catalogo["id"], stato="da_iniziare"
    )

    response = await client.patch(
        f"/api/v1/schede-alunno/{scheda['id']}/voci/{voce['id']}",
        json={"dettaglio": "nuovo dettaglio", "ordine": 5},
    )
    assert response.status_code == 200

    righe = await get_storico(db_session, scheda["id"])
    assert len(righe) == 1  # solo la riga di creazione, nessuna transizione


@pytest.mark.asyncio
async def test_storico_sopravvive_alla_cancellazione_della_voce(
    client: AsyncClient, db_session: AsyncSession
):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    categoria = await create_categoria_voce(client)
    voce_catalogo = await create_voce_catalogo(client, 1, categoria["codice"])
    voce = await create_voce_scheda(
        client, scheda["id"], voce_catalogo["id"], stato="acquisita"
    )

    delete = await client.delete(
        f"/api/v1/schede-alunno/{scheda['id']}/voci/{voce['id']}"
    )
    assert delete.status_code == 204

    righe = await get_storico(db_session, scheda["id"])
    assert len(righe) == 1
    assert righe[0].scheda_alunno_voce_id is None
    assert righe[0].scheda_alunno_id == scheda["id"]
    assert righe[0].voce_catalogo_id == voce_catalogo["id"]
    assert righe[0].stato_nuovo == "acquisita"


# ── Materiale didattico: struttura e CHECK constraint ────────────────────────


@pytest.mark.asyncio
async def test_materiale_check_constraint_arc_vuoto_rifiutato(
    client: AsyncClient, db_session: AsyncSession
):
    """Bypassando pydantic, il CHECK del DB deve impedire l'arc vuoto
    (né storage_key né url valorizzati) — stesso pattern già in uso per
    l'arc a 3 rami di ``Presenza``."""
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    db_session.add(SchedaAlunnoMateriale(scheda_alunno_id=scheda["id"], titolo="x"))
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_materiale_check_constraint_arc_entrambi_valorizzati_rifiutato(
    client: AsyncClient, db_session: AsyncSession
):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    db_session.add(
        SchedaAlunnoMateriale(
            scheda_alunno_id=scheda["id"],
            titolo="x",
            storage_key="schede-alunno/1/abc_file.pdf",
            url="https://example.com",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


# ── Materiale didattico: upload file ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_materiale_file(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    materiale = await create_materiale_file(client, scheda["id"])
    assert materiale["scheda_alunno_id"] == scheda["id"]
    assert materiale["titolo"] == "Spartito di studio"
    assert materiale["tipo"] == "file"
    assert materiale["nome_file_originale"] == "spartito.pdf"
    assert materiale["mime_type"] == "application/pdf"
    assert materiale["dimensione_bytes"] == len(b"contenuto del materiale di prova")
    assert materiale["url"] is None
    assert materiale["storage_key"] is not None


@pytest.mark.asyncio
async def test_upload_materiale_estensione_non_ammessa(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    response = await upload_materiale_file(
        client,
        scheda["id"],
        filename="virus.exe",
        content_type="application/x-msdownload",
    )
    assert response.status_code == 422
    assert "pdf" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_materiale_troppo_grande(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    import app.services.scheda_alunno_materiale_service as materiale_service_module

    monkeypatch.setattr(materiale_service_module, "DIMENSIONE_MASSIMA_BYTES", 10)

    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    response = await upload_materiale_file(client, scheda["id"], content=b"x" * 100)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_materiale_titolo_mancante(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    response = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/file",
        files={"file": ("spartito.pdf", b"contenuto", "application/pdf")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_materiale_scheda_not_found(client: AsyncClient):
    response = await upload_materiale_file(client, 999)
    assert response.status_code == 404


# ── Materiale didattico: link esterno ────────────────────────────────────────


@pytest.mark.asyncio
async def test_crea_materiale_link(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    materiale = await create_materiale_link(client, scheda["id"])
    assert materiale["tipo"] == "link"
    assert materiale["url"] == "https://youtube.com/watch?v=abc123"
    assert materiale["storage_key"] is None
    assert materiale["nome_file_originale"] is None


@pytest.mark.asyncio
async def test_crea_materiale_link_url_mancante(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    response = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/link",
        json={"titolo": "Senza url"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_scheda_alunno_espone_materiali_annidati(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    await create_materiale_file(client, scheda["id"], titolo="File")
    await create_materiale_link(client, scheda["id"], titolo="Link")

    response = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    assert response.status_code == 200
    materiali = response.json()["materiali"]
    assert len(materiali) == 2
    assert {m["tipo"] for m in materiali} == {"file", "link"}


# ── Materiale didattico: download ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_materiale_file(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    materiale = await create_materiale_file(
        client, scheda["id"], content=b"contenuto scaricabile"
    )

    response = await client.get(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/{materiale['id']}/download"
    )
    assert response.status_code == 200
    assert response.content == b"contenuto scaricabile"
    assert "spartito.pdf" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_download_materiale_link_rifiutato(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    materiale = await create_materiale_link(client, scheda["id"])

    response = await client.get(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/{materiale['id']}/download"
    )
    assert response.status_code == 422
    assert "url direttamente" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_materiale_not_found(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    response = await client.get(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/999/download"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_alunno_proprietario_scarica_il_proprio_materiale(client: AsyncClient):
    """Riusa gli scenari row-level già validati per la scheda: l'alunno
    proprietario, che non ha mai ``corsi:read``, scarica comunque il proprio
    materiale tramite lo stesso endpoint del personale corsi."""
    alunno, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    materiale = await create_materiale_file(client, scheda["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])
    response = await client.get(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/{materiale['id']}/download"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_alunno_terzo_non_scarica_materiale_altrui(client: AsyncClient):
    _alunno, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    materiale = await create_materiale_file(client, scheda["id"])
    estraneo = await create_persona(client, "Luca", "Neri")

    app.dependency_overrides[get_current_user] = lambda: _user(
        persona_id=estraneo["id"]
    )
    response = await client.get(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/{materiale['id']}/download"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_insegnante_di_altro_corso_scarica_comunque_il_materiale(
    client: AsyncClient,
):
    """La LETTURA non è ristretta per-corso (stesso perimetro già validato per
    la scheda in ``test_insegnante_di_altro_corso_legge_comunque_qualsiasi_scheda``):
    chi ha ``corsi:write``/``corsi:read`` scarica il materiale anche di un
    corso che non è il suo — solo la scrittura è vincolata al corso specifico."""
    insegnante_altro_corso = await create_persona(client, "Marco", "Neri")
    await create_corso(
        client,
        tipo_corso_codice=2,
        insegnante_persona_id=insegnante_altro_corso["id"],
    )
    _alunno, iscrizione = await setup_iscrizione(client)  # corso senza docenti
    scheda = await create_scheda(client, iscrizione["id"])
    materiale = await create_materiale_file(client, scheda["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:read", "corsi:write"}, persona_id=insegnante_altro_corso["id"]
    )
    response = await client.get(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/{materiale['id']}/download"
    )
    assert response.status_code == 200


# ── Materiale didattico: cancellazione ───────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_materiale_file_rimuove_anche_da_storage(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    materiale = await create_materiale_file(client, scheda["id"])
    storage_key = materiale["storage_key"]
    assert await storage.exists(storage_key)

    response = await client.delete(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/{materiale['id']}"
    )
    assert response.status_code == 204
    assert not await storage.exists(storage_key)

    riletta = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    assert riletta.json()["materiali"] == []


@pytest.mark.asyncio
async def test_delete_materiale_link(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    materiale = await create_materiale_link(client, scheda["id"])

    response = await client.delete(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/{materiale['id']}"
    )
    assert response.status_code == 204

    riletta = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    assert riletta.json()["materiali"] == []


@pytest.mark.asyncio
async def test_delete_materiale_not_found(client: AsyncClient):
    _persona, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])

    response = await client.delete(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/999"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_materiale_di_altra_scheda_non_raggiungibile(client: AsyncClient):
    corso = await create_corso(client)
    stato = await create_stato(client)
    persona1 = await create_persona(client, "Mario", "Rossi")
    persona2 = await create_persona(client, "Anna", "Bianchi")
    iscr1 = await create_iscrizione_corso(
        client, corso["id"], persona1["id"], stato["codice"]
    )
    iscr2 = await create_iscrizione_corso(
        client, corso["id"], persona2["id"], stato["codice"]
    )
    scheda1 = await create_scheda(client, iscr1["id"])
    scheda2 = await create_scheda(client, iscr2["id"])
    materiale = await create_materiale_link(client, scheda1["id"])

    response = await client.delete(
        f"/api/v1/schede-alunno/{scheda2['id']}/materiali/{materiale['id']}"
    )
    assert response.status_code == 404


# ── Materiale didattico: autorizzazione row-level (scrittura) ───────────────


@pytest.mark.asyncio
async def test_insegnante_di_altro_corso_non_scrive_materiali(client: AsyncClient):
    insegnante_altro_corso = await create_persona(client, "Marco", "Neri")
    await create_corso(
        client,
        tipo_corso_codice=2,
        insegnante_persona_id=insegnante_altro_corso["id"],
    )
    _alunno, iscrizione = await setup_iscrizione(client)  # corso senza docenti
    scheda = await create_scheda(client, iscrizione["id"])
    materiale = await create_materiale_link(client, scheda["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:read", "corsi:write"}, persona_id=insegnante_altro_corso["id"]
    )

    upload = await upload_materiale_file(client, scheda["id"])
    assert upload.status_code == 403

    link = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/link",
        json={"titolo": "x", "url": "https://example.com"},
    )
    assert link.status_code == 403

    delete = await client.delete(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/{materiale['id']}"
    )
    assert delete.status_code == 403


@pytest.mark.asyncio
async def test_alunno_proprietario_non_scrive_materiali(client: AsyncClient):
    alunno, iscrizione = await setup_iscrizione(client)
    scheda = await create_scheda(client, iscrizione["id"])
    materiale = await create_materiale_link(client, scheda["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])

    upload = await upload_materiale_file(client, scheda["id"])
    assert upload.status_code == 403

    link = await client.post(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/link",
        json={"titolo": "x", "url": "https://example.com"},
    )
    assert link.status_code == 403

    delete = await client.delete(
        f"/api/v1/schede-alunno/{scheda['id']}/materiali/{materiale['id']}"
    )
    assert delete.status_code == 403


@pytest.mark.asyncio
async def test_coordinatore_del_corso_scrive_materiali(client: AsyncClient):
    coordinatore = await create_persona(client, "Luigi", "Bruni")
    _alunno, iscrizione = await setup_iscrizione(
        client, coordinatore_persona_id=coordinatore["id"]
    )
    scheda = await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:write"}, persona_id=coordinatore["id"]
    )
    materiale = await create_materiale_link(client, scheda["id"])
    assert materiale["titolo"] == "Registrazione su YouTube"


@pytest.mark.asyncio
async def test_superuser_scrive_materiali_senza_essere_docente_del_corso(
    client: AsyncClient,
):
    insegnante = await create_persona(client, "Giulia", "Verdi")
    _alunno, iscrizione = await setup_iscrizione(
        client, insegnante_persona_id=insegnante["id"]
    )
    scheda = await create_scheda(client, iscrizione["id"])

    estraneo_al_corso = await create_persona(client, "Anna", "Bianchi")
    app.dependency_overrides[get_current_user] = lambda: _user(
        superuser=True, persona_id=estraneo_al_corso["id"]
    )
    materiale = await create_materiale_link(client, scheda["id"])
    assert materiale["titolo"] == "Registrazione su YouTube"


# ── Autovalutazioni: autorizzazione row-level, funzioni pure (card #218) ────
#
# Perimetro deliberatamente diverso da ``assert_puo_scrivere_scheda``: qui
# ``corsi:write`` non basta mai, conta solo l'identità dell'alunno
# proprietario. Vedi il docstring della funzione in ``rbac_row_level``.


def test_assert_puo_scrivere_autovalutazione_consente_alunno_proprietario():
    assert_puo_scrivere_autovalutazione(_user(persona_id=42), 42)


def test_assert_puo_scrivere_autovalutazione_nega_alunno_terzo():
    with pytest.raises(AccessoSchedaAlunnoNegatoError):
        assert_puo_scrivere_autovalutazione(_user(persona_id=7), 42)


def test_assert_puo_scrivere_autovalutazione_nega_corsi_write_da_solo():
    """Il cuore della card: a differenza di ``assert_puo_scrivere_scheda``,
    qui ``corsi:write`` non basta MAI, nemmeno per l'insegnante o il
    coordinatore del corso specifico — conta solo l'identità dell'alunno."""
    utente = _user(permessi={"corsi:write"}, persona_id=99)
    with pytest.raises(AccessoSchedaAlunnoNegatoError):
        assert_puo_scrivere_autovalutazione(utente, 42)


def test_assert_puo_scrivere_autovalutazione_consente_superuser():
    assert_puo_scrivere_autovalutazione(_user(superuser=True, persona_id=99), 42)


def test_assert_puo_scrivere_autovalutazione_nega_utente_senza_persona_collegata():
    with pytest.raises(AccessoSchedaAlunnoNegatoError):
        assert_puo_scrivere_autovalutazione(_user(persona_id=None), 42)


# ── Autovalutazioni: CRUD self-service dell'alunno ───────────────────────────


async def create_autovalutazione(
    client: AsyncClient,
    iscrizione_corso_id: int,
    testo: str = "Oggi le scale sono andate meglio",
) -> dict:
    response = await client.post(
        f"/api/v1/schede-alunno/me/{iscrizione_corso_id}/autovalutazioni",
        json={"testo": testo},
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_alunno_proprietario_crea_autovalutazione(client: AsyncClient):
    alunno, iscrizione = await setup_iscrizione(client)
    await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])
    data = await create_autovalutazione(
        client, iscrizione["id"], testo="Oggi ho suonato meglio le scale"
    )

    assert data["testo"] == "Oggi ho suonato meglio le scale"
    assert data["persona_id"] == alunno["id"]
    assert data["data_creazione"] is not None
    assert data["data_modifica"] is None


@pytest.mark.asyncio
async def test_alunno_proprietario_modifica_autovalutazione_valorizza_data_modifica(
    client: AsyncClient,
):
    alunno, iscrizione = await setup_iscrizione(client)
    await create_scheda(client, iscrizione["id"])
    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])
    autovalutazione = await create_autovalutazione(client, iscrizione["id"])
    assert autovalutazione["data_modifica"] is None

    response = await client.patch(
        f"/api/v1/schede-alunno/me/{iscrizione['id']}/autovalutazioni/"
        f"{autovalutazione['id']}",
        json={"testo": "Ripensandoci, devo lavorare ancora sull'intonazione"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["testo"] == "Ripensandoci, devo lavorare ancora sull'intonazione"
    assert data["data_modifica"] is not None
    assert data["data_creazione"] == autovalutazione["data_creazione"]


@pytest.mark.asyncio
async def test_alunno_proprietario_cancella_autovalutazione(client: AsyncClient):
    alunno, iscrizione = await setup_iscrizione(client)
    await create_scheda(client, iscrizione["id"])
    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])
    autovalutazione = await create_autovalutazione(client, iscrizione["id"])

    response = await client.delete(
        f"/api/v1/schede-alunno/me/{iscrizione['id']}/autovalutazioni/"
        f"{autovalutazione['id']}"
    )
    assert response.status_code == 204

    propria = await client.get(f"/api/v1/schede-alunno/me/{iscrizione['id']}")
    assert propria.json()["autovalutazioni"] == []


@pytest.mark.asyncio
async def test_creazione_autovalutazione_su_scheda_non_ancora_creata(
    client: AsyncClient,
):
    """L'alunno non può autovalutarsi su una scheda che l'insegnante non ha
    ancora creato: 404 chiaro, non un 403 confuso con l'autorizzazione."""
    alunno, iscrizione = await setup_iscrizione(client)
    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])

    response = await client.post(
        f"/api/v1/schede-alunno/me/{iscrizione['id']}/autovalutazioni",
        json={"testo": "x"},
    )
    assert response.status_code == 404


# ── Autovalutazioni: autorizzazione row-level end-to-end ────────────────────


@pytest.mark.asyncio
async def test_insegnante_con_corsi_write_del_corso_non_scrive_autovalutazione(
    client: AsyncClient,
):
    """Il cuore della card: il bypass di ``assert_puo_scrivere_scheda`` per
    chi ha ``corsi:write`` ed è insegnante/coordinatore del corso specifico
    NON si applica qui — l'autovalutazione è scrivibile solo dall'alunno."""
    insegnante = await create_persona(client, "Giulia", "Verdi")
    alunno, iscrizione = await setup_iscrizione(
        client, insegnante_persona_id=insegnante["id"]
    )
    await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])
    autovalutazione = await create_autovalutazione(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:read", "corsi:write"}, persona_id=insegnante["id"]
    )

    post = await client.post(
        f"/api/v1/schede-alunno/me/{iscrizione['id']}/autovalutazioni",
        json={"testo": "voto io per lui"},
    )
    assert post.status_code == 403

    patch = await client.patch(
        f"/api/v1/schede-alunno/me/{iscrizione['id']}/autovalutazioni/"
        f"{autovalutazione['id']}",
        json={"testo": "alterato"},
    )
    assert patch.status_code == 403

    delete = await client.delete(
        f"/api/v1/schede-alunno/me/{iscrizione['id']}/autovalutazioni/"
        f"{autovalutazione['id']}"
    )
    assert delete.status_code == 403


@pytest.mark.asyncio
async def test_insegnante_di_altro_corso_non_scrive_autovalutazione(
    client: AsyncClient,
):
    insegnante_altro_corso = await create_persona(client, "Marco", "Neri")
    await create_corso(
        client,
        tipo_corso_codice=2,
        insegnante_persona_id=insegnante_altro_corso["id"],
    )
    _alunno, iscrizione = await setup_iscrizione(client)  # corso senza docenti
    await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:read", "corsi:write"}, persona_id=insegnante_altro_corso["id"]
    )
    response = await client.post(
        f"/api/v1/schede-alunno/me/{iscrizione['id']}/autovalutazioni",
        json={"testo": "x"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_alunno_terzo_non_scrive_autovalutazione_altrui(client: AsyncClient):
    _alunno, iscrizione = await setup_iscrizione(client)
    await create_scheda(client, iscrizione["id"])
    estraneo = await create_persona(client, "Luca", "Neri")

    app.dependency_overrides[get_current_user] = lambda: _user(
        persona_id=estraneo["id"]
    )
    response = await client.post(
        f"/api/v1/schede-alunno/me/{iscrizione['id']}/autovalutazioni",
        json={"testo": "x"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_superuser_scrive_autovalutazione_senza_essere_alunno(
    client: AsyncClient,
):
    """Il superuser bypassa la restrizione, stesso pattern del resto del
    modulo — anche se non è l'alunno proprietario della scheda."""
    _alunno, iscrizione = await setup_iscrizione(client)
    await create_scheda(client, iscrizione["id"])
    estraneo = await create_persona(client, "Anna", "Bianchi")

    app.dependency_overrides[get_current_user] = lambda: _user(
        superuser=True, persona_id=estraneo["id"]
    )
    data = await create_autovalutazione(
        client, iscrizione["id"], testo="nota inserita dal superuser"
    )
    assert data["persona_id"] == estraneo["id"]


@pytest.mark.asyncio
async def test_utente_senza_persona_collegata_non_scrive_autovalutazione(
    client: AsyncClient,
):
    _alunno, iscrizione = await setup_iscrizione(client)
    await create_scheda(client, iscrizione["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=None)
    response = await client.post(
        f"/api/v1/schede-alunno/me/{iscrizione['id']}/autovalutazioni",
        json={"testo": "x"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_lettura_autovalutazioni_insegnante_alunno_proprietario_e_terzo(
    client: AsyncClient,
):
    """La LETTURA riusa il perimetro già esistente di
    ``assert_puo_leggere_scheda`` (invariato da questa card): l'insegnante
    con ``corsi:read`` e l'alunno proprietario vedono le autovalutazioni,
    l'alunno terzo no."""
    insegnante = await create_persona(client, "Giulia", "Verdi")
    alunno, iscrizione = await setup_iscrizione(
        client, insegnante_persona_id=insegnante["id"]
    )
    scheda = await create_scheda(client, iscrizione["id"])
    estraneo = await create_persona(client, "Luca", "Neri")

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])
    await create_autovalutazione(client, iscrizione["id"], testo="nota personale")

    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"corsi:read"}, persona_id=insegnante["id"]
    )
    lettura_insegnante = await client.get(f"/api/v1/schede-alunno/{scheda['id']}")
    assert lettura_insegnante.status_code == 200
    assert len(lettura_insegnante.json()["autovalutazioni"]) == 1

    app.dependency_overrides[get_current_user] = lambda: _user(persona_id=alunno["id"])
    lettura_alunno = await client.get(f"/api/v1/schede-alunno/me/{iscrizione['id']}")
    assert lettura_alunno.status_code == 200
    assert lettura_alunno.json()["autovalutazioni"][0]["testo"] == "nota personale"

    app.dependency_overrides[get_current_user] = lambda: _user(
        persona_id=estraneo["id"]
    )
    lettura_terzo = await client.get(f"/api/v1/schede-alunno/me/{iscrizione['id']}")
    assert lettura_terzo.status_code == 403


# ── Autovalutazioni: contorni del row-level ──────────────────────────────────


@pytest.mark.asyncio
async def test_autovalutazione_di_altra_scheda_non_raggiungibile(client: AsyncClient):
    """L'id deve appartenere ESATTAMENTE alla scheda dell'iscrizione indicata
    nell'URL, anche se il chiamante è proprietario di una scheda diversa —
    stesso principio già applicato per le voci di programma."""
    corso = await create_corso(client)
    stato = await create_stato(client)
    persona1 = await create_persona(client, "Mario", "Rossi")
    persona2 = await create_persona(client, "Anna", "Bianchi")
    iscr1 = await create_iscrizione_corso(
        client, corso["id"], persona1["id"], stato["codice"]
    )
    iscr2 = await create_iscrizione_corso(
        client, corso["id"], persona2["id"], stato["codice"]
    )
    await create_scheda(client, iscr1["id"])
    await create_scheda(client, iscr2["id"])

    app.dependency_overrides[get_current_user] = lambda: _user(
        persona_id=persona1["id"]
    )
    autovalutazione = await create_autovalutazione(client, iscr1["id"])

    # persona2 è proprietaria di una scheda DIVERSA: autorizzata sulla
    # propria iscrizione, ma l'id richiesto appartiene alla scheda di iscr1.
    app.dependency_overrides[get_current_user] = lambda: _user(
        persona_id=persona2["id"]
    )
    patch = await client.patch(
        f"/api/v1/schede-alunno/me/{iscr2['id']}/autovalutazioni/"
        f"{autovalutazione['id']}",
        json={"testo": "alterato"},
    )
    assert patch.status_code == 404

    delete = await client.delete(
        f"/api/v1/schede-alunno/me/{iscr2['id']}/autovalutazioni/"
        f"{autovalutazione['id']}"
    )
    assert delete.status_code == 404
