from __future__ import annotations

from io import BytesIO

import pytest
from httpx import AsyncClient
from reportlab.pdfgen import canvas
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.persona import Persona
from app.models.presenza import Presenza


def make_pdf(text: str) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, text)
    c.showPage()
    c.save()
    return buf.getvalue()


async def create_indirizzo(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/indirizzi/",
        json={"tipo_indirizzo_codice": 4, "prima_riga": "Piazza Chiesa"},
    )
    return response.json()


async def create_servizio(client: AsyncClient, **overrides) -> dict:
    indirizzo = await create_indirizzo(client)
    payload = {
        "banda_codice": 1,
        "anno": 2026,
        "descrizione_servizio": "Concerto estivo",
        "data_servizio": "2026-07-20T21:00:00",
        "indirizzo_id": indirizzo["id"],
    }
    payload.update(overrides)
    response = await client.post("/api/v1/servizi/", json=payload)
    return response.json()


def prova_payload(**overrides) -> dict:
    payload = {"banda_codice": 1, "data_prova": "2026-07-10T20:30:00"}
    payload.update(overrides)
    return payload


async def create_prova(client: AsyncClient, **overrides) -> dict:
    response = await client.post("/api/v1/prove/", json=prova_payload(**overrides))
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


async def create_esterno(
    client: AsyncClient, persona_id: int, strumento_codice: int
) -> dict:
    response = await client.post(
        "/api/v1/esterni/",
        json={
            "persona_id": persona_id,
            "strumento_codice": strumento_codice,
        },
    )
    return response.json()


async def create_nome_parte(client: AsyncClient, nome: str) -> dict:
    response = await client.post(
        "/api/v1/nome-parti/",
        json={"nome": nome, "tipo_spartito_codice": 1, "banda_codice": 1},
    )
    assert response.status_code == 201
    return response.json()


async def upload_documento(client: AsyncClient, content: bytes, filename: str) -> dict:
    response = await client.post(
        "/api/v1/documenti/",
        files=[("file", (filename, content, "application/pdf"))],
    )
    assert response.status_code == 201
    return response.json()


async def create_spartito(
    client: AsyncClient,
    nome_parte_id: int,
    documento_id: int | None,
    strumento_codice: int | None,
) -> dict:
    payload = {
        "banda_codice": 1,
        "tipo_spartito_codice": 1,
        "nome_parte_id": nome_parte_id,
    }
    if documento_id is not None:
        payload["documento_id"] = documento_id
    if strumento_codice is not None:
        payload["strumento_codice"] = strumento_codice
    response = await client.post("/api/v1/spartiti/", json=payload)
    assert response.status_code == 201
    return response.json()


STRUMENTO_TROMBA = 5


# ── CRUD Prova ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_prova_standalone(client: AsyncClient):
    response = await client.post("/api/v1/prove/", json=prova_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["servizio_id"] is None
    assert data["indirizzo_id"] is None


@pytest.mark.asyncio
async def test_create_prova_orientata_a_servizio(client: AsyncClient):
    servizio = await create_servizio(client)
    response = await client.post(
        "/api/v1/prove/", json=prova_payload(servizio_id=servizio["id"])
    )
    assert response.status_code == 201
    data = response.json()
    assert data["servizio_id"] == servizio["id"]
    assert data["servizio"]["descrizione_servizio"] == "Concerto estivo"


@pytest.mark.asyncio
async def test_create_prova_servizio_not_found(client: AsyncClient):
    response = await client.post("/api/v1/prove/", json=prova_payload(servizio_id=999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_prova_indirizzo_not_found(client: AsyncClient):
    response = await client.post("/api/v1/prove/", json=prova_payload(indirizzo_id=999))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_prova_not_found(client: AsyncClient):
    response = await client.get("/api/v1/prove/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_prova(client: AsyncClient):
    prova = await create_prova(client)
    response = await client.patch(
        f"/api/v1/prove/{prova['id']}", json={"note": "Prova aggiunta libretto marce"}
    )
    assert response.status_code == 200
    assert response.json()["note"] == "Prova aggiunta libretto marce"


@pytest.mark.asyncio
async def test_update_prova_aggiunge_indirizzo(client: AsyncClient):
    """Regressione: stesso bug scoperto in ServizioRepository.update() (la
    sessione usa expire_on_commit=False, quindi senza un expire esplicito la
    rilettura post-commit restituisce le relazioni stantie precedenti
    all'update). Una PATCH che assegna indirizzo_id a una prova che non ne
    aveva uno deve restituire anche l'oggetto indirizzo annidato popolato."""
    prova = await create_prova(client)
    assert prova["indirizzo_id"] is None
    indirizzo = await create_indirizzo(client)

    response = await client.patch(
        f"/api/v1/prove/{prova['id']}", json={"indirizzo_id": indirizzo["id"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["indirizzo_id"] == indirizzo["id"]
    assert data["indirizzo"] is not None
    assert data["indirizzo"]["id"] == indirizzo["id"]


@pytest.mark.asyncio
async def test_delete_prova(client: AsyncClient):
    prova = await create_prova(client)
    response = await client.delete(f"/api/v1/prove/{prova['id']}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/prove/{prova['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_list_prove_filtro_servizio(client: AsyncClient):
    servizio = await create_servizio(client)
    await create_prova(client, servizio_id=servizio["id"])
    await create_prova(client)

    response = await client.get(
        "/api/v1/prove/", params={"servizio_id": servizio["id"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 1
    assert data["items"][0]["servizio_id"] == servizio["id"]


# ── Arc esclusivo su Presenza/RepertorioItem ────────────────────────────────


@pytest.mark.asyncio
async def test_create_presenza_con_servizio_e_prova_rifiutata(client: AsyncClient):
    persona = await create_persona(client)
    servizio = await create_servizio(client)
    prova = await create_prova(client)
    response = await client.post(
        "/api/v1/presenze/",
        json={
            "persona_id": persona["id"],
            "servizio_id": servizio["id"],
            "prova_id": prova["id"],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_presenza_senza_servizio_ne_prova_rifiutata(client: AsyncClient):
    persona = await create_persona(client)
    response = await client.post(
        "/api/v1/presenze/", json={"persona_id": persona["id"]}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_repertorio_item_con_servizio_e_prova_rifiutata(
    client: AsyncClient,
):
    nome_parte = await create_nome_parte(client, "Marcia")
    servizio = await create_servizio(client)
    prova = await create_prova(client)
    response = await client.post(
        "/api/v1/repertorio/",
        json={
            "nome_parte_id": nome_parte["id"],
            "servizio_id": servizio["id"],
            "prova_id": prova["id"],
            "ordine": 1,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_repertorio_item_senza_servizio_ne_prova_rifiutata(
    client: AsyncClient,
):
    nome_parte = await create_nome_parte(client, "Marcia")
    response = await client.post(
        "/api/v1/repertorio/",
        json={"nome_parte_id": nome_parte["id"], "ordine": 1},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_presenza_check_constraint_a_livello_db(db_session: AsyncSession):
    """Anche bypassando la validazione pydantic (es. codice interno che
    costruisce il modello direttamente) il CHECK del DB deve impedire sia
    l'arc vuoto sia l'arc doppio."""
    persona = Persona(banda_codice=1, nome="Mario", cognome="Rossi")
    db_session.add(persona)
    await db_session.flush()

    db_session.add(Presenza(persona_id=persona.id))
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


# ── Riuso organico/repertorio/libretto per Prova ────────────────────────────


@pytest.mark.asyncio
async def test_organico_e_repertorio_prova_via_presenze_e_repertorio_router(
    client: AsyncClient,
):
    prova = await create_prova(client)
    persona = await create_persona(client)
    presenza = await client.post(
        "/api/v1/presenze/",
        json={"persona_id": persona["id"], "prova_id": prova["id"]},
    )
    assert presenza.status_code == 201
    assert presenza.json()["prova_id"] == prova["id"]

    organico = await client.get(f"/api/v1/presenze/prova/{prova['id']}")
    assert organico.status_code == 200
    assert organico.json()["meta"]["total_items"] == 1

    nome_parte = await create_nome_parte(client, "Marcia")
    item = await client.post(
        "/api/v1/repertorio/",
        json={"nome_parte_id": nome_parte["id"], "prova_id": prova["id"], "ordine": 1},
    )
    assert item.status_code == 201
    assert item.json()["prova_id"] == prova["id"]

    repertorio = await client.get(f"/api/v1/repertorio/prova/{prova['id']}")
    assert repertorio.status_code == 200
    assert repertorio.json()["meta"]["total_items"] == 1


@pytest.mark.asyncio
async def test_organico_prova_not_found(client: AsyncClient):
    response = await client.get("/api/v1/presenze/prova/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_repertorio_prova_not_found(client: AsyncClient):
    response = await client.get("/api/v1/repertorio/prova/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_libretto_prova_generato_correttamente(client: AsyncClient):
    prova = await create_prova(client)
    persona = await create_persona(client, "Mario", "Trombetta")
    esterno = await create_esterno(client, persona["id"], STRUMENTO_TROMBA)
    await client.post(
        "/api/v1/presenze/",
        json={"persona_id": esterno["persona_id"], "prova_id": prova["id"]},
    )

    brano = await create_nome_parte(client, "Marcia Trionfale")
    await client.post(
        "/api/v1/repertorio/",
        json={"nome_parte_id": brano["id"], "prova_id": prova["id"], "ordine": 1},
    )
    doc = await upload_documento(client, make_pdf("MARCIA_TROMBA"), "marcia.pdf")
    await create_spartito(client, brano["id"], doc["id"], STRUMENTO_TROMBA)

    response = await client.get(
        f"/api/v1/prove/{prova['id']}/libretto",
        params={"persona_id": esterno["persona_id"]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_libretto_prova_senza_organico(client: AsyncClient):
    prova = await create_prova(client)
    brano = await create_nome_parte(client, "Marcia")
    await client.post(
        "/api/v1/repertorio/",
        json={"nome_parte_id": brano["id"], "prova_id": prova["id"], "ordine": 1},
    )
    response = await client.get(f"/api/v1/prove/{prova['id']}/libretto")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_libretto_prova_not_found(client: AsyncClient):
    response = await client.get("/api/v1/prove/999/libretto")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_libretto_prova_spartito_segnaposto_non_oscura_quello_con_documento(
    client: AsyncClient,
):
    """Regressione: uno Spartito segnaposto senza documento, registrato per
    lo stesso strumento prima di quello vero (``Spartito`` non ha vincolo di
    unicità su nome_parte_id+strumento_codice), non deve far risultare il
    brano "mancante" se esiste un'altra riga con lo stesso strumento e il
    documento caricato. Stesso bug del path Servizio, riprodotto qui sulla
    Prova perché è lo scenario segnalato originariamente."""
    prova = await create_prova(client)
    persona = await create_persona(client, "Mario", "Trombetta")
    esterno = await create_esterno(client, persona["id"], STRUMENTO_TROMBA)
    await client.post(
        "/api/v1/presenze/",
        json={"persona_id": esterno["persona_id"], "prova_id": prova["id"]},
    )

    brano = await create_nome_parte(client, "Marcia Trionfale")
    await client.post(
        "/api/v1/repertorio/",
        json={"nome_parte_id": brano["id"], "prova_id": prova["id"], "ordine": 1},
    )

    # Segnaposto: brano registrato prima di avere il file.
    await create_spartito(client, brano["id"], None, STRUMENTO_TROMBA)
    # Spartito vero, aggiunto dopo come riga separata per lo stesso strumento.
    doc = await upload_documento(client, make_pdf("MARCIA_TROMBA"), "marcia.pdf")
    await create_spartito(client, brano["id"], doc["id"], STRUMENTO_TROMBA)

    response = await client.get(
        f"/api/v1/prove/{prova['id']}/libretto",
        params={"persona_id": esterno["persona_id"]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
