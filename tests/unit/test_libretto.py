from __future__ import annotations

import json
import zipfile
from io import BytesIO

import pytest
from httpx import AsyncClient
from pypdf import PdfReader
from reportlab.pdfgen import canvas


def make_pdf(text: str) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, text)
    c.showPage()
    c.save()
    return buf.getvalue()


def pdf_pages_text(content: bytes) -> list[str]:
    reader = PdfReader(BytesIO(content))
    return [page.extract_text() for page in reader.pages]


async def upload_documento(client: AsyncClient, content: bytes, filename: str) -> dict:
    response = await client.post(
        "/api/v1/documenti/",
        files=[("file", (filename, content, "application/pdf"))],
    )
    assert response.status_code == 201
    return response.json()


async def create_servizio(client: AsyncClient) -> dict:
    indirizzo = await client.post(
        "/api/v1/indirizzi/",
        json={"tipo_indirizzo_codice": 4, "prima_riga": "Piazza Chiesa"},
    )
    response = await client.post(
        "/api/v1/servizi/",
        json={
            "banda_codice": 1,
            "anno": 2026,
            "descrizione_servizio": "Concerto estivo",
            "data_servizio": "2026-07-20T21:00:00",
            "indirizzo_id": indirizzo.json()["id"],
        },
    )
    return response.json()


async def create_persona(client: AsyncClient, nome: str, cognome: str) -> dict:
    response = await client.post(
        "/api/v1/persone/",
        json={"banda_codice": 1, "nome": nome, "cognome": cognome},
    )
    return response.json()


async def create_esterno(
    client: AsyncClient, persona_id: int, strumento_codice: int, codice: str
) -> dict:
    response = await client.post(
        "/api/v1/esterni/",
        json={
            "persona_id": persona_id,
            "codice_esterno": codice,
            "strumento_codice": strumento_codice,
        },
    )
    return response.json()


async def create_socio(
    client: AsyncClient,
    persona_id: int,
    codice: str,
    strumento_codice: int | None,
) -> dict:
    payload = {
        "persona_id": persona_id,
        "codice_socio": codice,
        "banda_codice": 1,
        "ruolo_banda_codice": 10,
    }
    if strumento_codice is not None:
        payload["strumento_codice"] = strumento_codice
    response = await client.post("/api/v1/soci/", json=payload)
    return response.json()


async def create_presenza(
    client: AsyncClient, persona_id: int, servizio_id: int
) -> dict:
    response = await client.post(
        "/api/v1/presenze/",
        json={"servizio_id": servizio_id, "persona_id": persona_id},
    )
    assert response.status_code == 201
    return response.json()


async def create_nome_parte(client: AsyncClient, nome: str) -> dict:
    response = await client.post(
        "/api/v1/nome-parti/",
        json={"nome": nome, "tipo_spartito_codice": 1, "banda_codice": 1},
    )
    assert response.status_code == 201
    return response.json()


async def create_repertorio_item(
    client: AsyncClient, servizio_id: int, nome_parte_id: int, ordine: int
) -> dict:
    response = await client.post(
        "/api/v1/repertorio/",
        json={
            "servizio_id": servizio_id,
            "nome_parte_id": nome_parte_id,
            "ordine": ordine,
        },
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
STRUMENTO_CLARINETTO = 6


@pytest.mark.asyncio
async def test_libretto_organico_due_persone_due_brani(client: AsyncClient):
    servizio = await create_servizio(client)

    tromba_p = await create_persona(client, "Mario", "Trombetta")
    tromba = await create_esterno(client, tromba_p["id"], STRUMENTO_TROMBA, "E001")
    clarinetto_p = await create_persona(client, "Anna", "Clarinetti")
    clarinetto = await create_esterno(
        client, clarinetto_p["id"], STRUMENTO_CLARINETTO, "E002"
    )

    await create_presenza(client, tromba["persona_id"], servizio["id"])
    await create_presenza(client, clarinetto["persona_id"], servizio["id"])

    brano1 = await create_nome_parte(client, "Marcia Trionfale")
    brano2 = await create_nome_parte(client, "Inno alla Gioia")
    await create_repertorio_item(client, servizio["id"], brano1["id"], ordine=2)
    await create_repertorio_item(client, servizio["id"], brano2["id"], ordine=1)

    for brano, label in ((brano1, "MARCIA"), (brano2, "INNO")):
        for strumento, nome_strumento in (
            (STRUMENTO_TROMBA, "TROMBA"),
            (STRUMENTO_CLARINETTO, "CLARINETTO"),
        ):
            doc = await upload_documento(
                client, make_pdf(f"{label}_{nome_strumento}"), f"{label}.pdf"
            )
            await create_spartito(client, brano["id"], doc["id"], strumento)

    # Libretto tromba: atteso ordine INNO (ordine=1), MARCIA (ordine=2).
    response = await client.get(
        f"/api/v1/servizi/{servizio['id']}/libretto",
        params={"persona_id": tromba["persona_id"]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    pages = pdf_pages_text(response.content)
    assert len(pages) == 2
    assert "INNO_TROMBA" in pages[0]
    assert "MARCIA_TROMBA" in pages[1]

    response = await client.get(
        f"/api/v1/servizi/{servizio['id']}/libretto",
        params={"persona_id": clarinetto["persona_id"]},
    )
    pages = pdf_pages_text(response.content)
    assert len(pages) == 2
    assert "INNO_CLARINETTO" in pages[0]
    assert "MARCIA_CLARINETTO" in pages[1]


@pytest.mark.asyncio
async def test_libretto_spartito_strumento_nullo_incluso_per_tutti(
    client: AsyncClient,
):
    servizio = await create_servizio(client)
    persona = await create_persona(client, "Mario", "Trombetta")
    esterno = await create_esterno(client, persona["id"], STRUMENTO_TROMBA, "E001")
    await create_presenza(client, esterno["persona_id"], servizio["id"])

    brano = await create_nome_parte(client, "Corale")
    await create_repertorio_item(client, servizio["id"], brano["id"], ordine=1)
    doc = await upload_documento(client, make_pdf("CORALE_UNICO"), "corale.pdf")
    # Nessuno spartito specifico per tromba: solo il PDF a strumento nullo.
    await create_spartito(client, brano["id"], doc["id"], None)

    response = await client.get(
        f"/api/v1/servizi/{servizio['id']}/libretto",
        params={"persona_id": esterno["persona_id"]},
    )
    assert response.status_code == 200
    pages = pdf_pages_text(response.content)
    assert len(pages) == 1
    assert "CORALE_UNICO" in pages[0]
    assert "X-Brani-Mancanti" not in response.headers


@pytest.mark.asyncio
async def test_libretto_brano_mancante_segnalato_esplicitamente(client: AsyncClient):
    servizio = await create_servizio(client)
    persona = await create_persona(client, "Mario", "Trombetta")
    esterno = await create_esterno(client, persona["id"], STRUMENTO_TROMBA, "E001")
    await create_presenza(client, esterno["persona_id"], servizio["id"])

    brano_ok = await create_nome_parte(client, "Marcia")
    brano_mancante = await create_nome_parte(client, "Assolo Clarinetto")
    await create_repertorio_item(client, servizio["id"], brano_ok["id"], ordine=1)
    await create_repertorio_item(client, servizio["id"], brano_mancante["id"], ordine=2)

    doc = await upload_documento(client, make_pdf("MARCIA_TROMBA"), "marcia.pdf")
    await create_spartito(client, brano_ok["id"], doc["id"], STRUMENTO_TROMBA)
    # Per "Assolo Clarinetto" esiste solo lo spartito per clarinetto, non per
    # tromba.
    doc2 = await upload_documento(client, make_pdf("ASSOLO_CL"), "assolo.pdf")
    await create_spartito(
        client, brano_mancante["id"], doc2["id"], STRUMENTO_CLARINETTO
    )

    response = await client.get(
        f"/api/v1/servizi/{servizio['id']}/libretto",
        params={"persona_id": esterno["persona_id"]},
    )
    assert response.status_code == 200
    pages = pdf_pages_text(response.content)
    assert len(pages) == 1
    assert "MARCIA_TROMBA" in pages[0]
    assert "Assolo Clarinetto" in response.headers["X-Brani-Mancanti"]

    # Nel download collettivo lo stesso deve comparire nel report.json dello zip.
    response = await client.get(f"/api/v1/servizi/{servizio['id']}/libretto")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(BytesIO(response.content)) as zf:
        report = json.loads(zf.read("report.json"))
    voce = next(
        p for p in report["persone"] if p["persona_id"] == esterno["persona_id"]
    )
    assert "Assolo Clarinetto" in voce["brani_mancanti"]


@pytest.mark.asyncio
async def test_libretto_socio_senza_strumento_indeterminato_non_escluso(
    client: AsyncClient,
):
    """Un socio senza strumento tracciato non va escluso silenziosamente: il
    suo libretto include solo gli spartiti a strumento nullo, e tutti i brani
    senza uno spartito 'universale' sono segnalati come mancanti."""
    servizio = await create_servizio(client)
    persona = await create_persona(client, "Luca", "Senzastrumento")
    socio = await create_socio(client, persona["id"], "S001", strumento_codice=None)
    await create_presenza(client, socio["persona_id"], servizio["id"])

    brano_universale = await create_nome_parte(client, "Inno")
    brano_specifico = await create_nome_parte(client, "Assolo Tromba")
    await create_repertorio_item(
        client, servizio["id"], brano_universale["id"], ordine=1
    )
    await create_repertorio_item(
        client, servizio["id"], brano_specifico["id"], ordine=2
    )

    doc = await upload_documento(client, make_pdf("INNO_UNICO"), "inno.pdf")
    await create_spartito(client, brano_universale["id"], doc["id"], None)
    doc2 = await upload_documento(client, make_pdf("ASSOLO_TROMBA"), "assolo.pdf")
    await create_spartito(client, brano_specifico["id"], doc2["id"], STRUMENTO_TROMBA)

    response = await client.get(
        f"/api/v1/servizi/{servizio['id']}/libretto",
        params={"persona_id": socio["persona_id"]},
    )
    assert response.status_code == 200
    pages = pdf_pages_text(response.content)
    assert len(pages) == 1
    assert "INNO_UNICO" in pages[0]
    assert "Assolo Tromba" in response.headers["X-Brani-Mancanti"]


@pytest.mark.asyncio
async def test_libretto_servizio_senza_organico(client: AsyncClient):
    servizio = await create_servizio(client)
    brano = await create_nome_parte(client, "Marcia")
    await create_repertorio_item(client, servizio["id"], brano["id"], ordine=1)

    response = await client.get(f"/api/v1/servizi/{servizio['id']}/libretto")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_libretto_servizio_senza_repertorio(client: AsyncClient):
    servizio = await create_servizio(client)
    persona = await create_persona(client, "Mario", "Trombetta")
    esterno = await create_esterno(client, persona["id"], STRUMENTO_TROMBA, "E001")
    await create_presenza(client, esterno["persona_id"], servizio["id"])

    response = await client.get(f"/api/v1/servizi/{servizio['id']}/libretto")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_libretto_persona_id_non_in_organico(client: AsyncClient):
    servizio = await create_servizio(client)
    persona = await create_persona(client, "Mario", "Trombetta")
    esterno = await create_esterno(client, persona["id"], STRUMENTO_TROMBA, "E001")
    await create_presenza(client, esterno["persona_id"], servizio["id"])
    brano = await create_nome_parte(client, "Marcia")
    await create_repertorio_item(client, servizio["id"], brano["id"], ordine=1)

    response = await client.get(
        f"/api/v1/servizi/{servizio['id']}/libretto",
        params={"persona_id": 999999},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_libretto_servizio_not_found(client: AsyncClient):
    response = await client.get("/api/v1/servizi/999999/libretto")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_libretto_persona_senza_nessuno_spartito_download_singolo(
    client: AsyncClient,
):
    """Se per una persona non esiste nessuno spartito in tutto il repertorio,
    il download del singolo libretto è un errore esplicito, non un PDF vuoto."""
    servizio = await create_servizio(client)
    persona = await create_persona(client, "Mario", "Trombetta")
    esterno = await create_esterno(client, persona["id"], STRUMENTO_TROMBA, "E001")
    await create_presenza(client, esterno["persona_id"], servizio["id"])

    brano = await create_nome_parte(client, "Assolo Clarinetto")
    await create_repertorio_item(client, servizio["id"], brano["id"], ordine=1)
    doc = await upload_documento(client, make_pdf("ASSOLO_CL"), "assolo.pdf")
    await create_spartito(client, brano["id"], doc["id"], STRUMENTO_CLARINETTO)

    response = await client.get(
        f"/api/v1/servizi/{servizio['id']}/libretto",
        params={"persona_id": esterno["persona_id"]},
    )
    assert response.status_code == 404

    # Nel collettivo invece la persona compare nel report come "senza spartiti",
    # senza bloccare il libretto degli altri.
    response = await client.get(f"/api/v1/servizi/{servizio['id']}/libretto")
    assert response.status_code == 200
    with zipfile.ZipFile(BytesIO(response.content)) as zf:
        report = json.loads(zf.read("report.json"))
        assert zf.namelist() == ["report.json"]
    voce = report["persone"][0]
    assert voce["file"] is None
    assert voce["errore"] == "nessuno spartito trovato"


@pytest.mark.asyncio
async def test_libretto_spartito_segnaposto_non_oscura_quello_con_documento(
    client: AsyncClient,
):
    """``Spartito`` non ha vincolo di unicità su (nome_parte_id,
    strumento_codice): è possibile registrare prima un segnaposto senza
    documento ("esiste il brano ma non ancora il file", workflow supportato
    da NomeParte) e poi aggiungere, come riga separata, lo spartito vero con
    il PDF per lo stesso strumento. La selezione deve preferire quello con il
    documento, non il primo della lista."""
    servizio = await create_servizio(client)
    persona = await create_persona(client, "Mario", "Trombetta")
    esterno = await create_esterno(client, persona["id"], STRUMENTO_TROMBA, "E001")
    await create_presenza(client, esterno["persona_id"], servizio["id"])

    brano = await create_nome_parte(client, "Marcia Trionfale")
    await create_repertorio_item(client, servizio["id"], brano["id"], ordine=1)

    # Segnaposto: brano registrato prima di avere il file.
    await create_spartito(client, brano["id"], None, STRUMENTO_TROMBA)
    # Spartito vero, aggiunto dopo come riga separata per lo stesso strumento.
    doc = await upload_documento(client, make_pdf("MARCIA_TROMBA"), "marcia.pdf")
    await create_spartito(client, brano["id"], doc["id"], STRUMENTO_TROMBA)

    response = await client.get(
        f"/api/v1/servizi/{servizio['id']}/libretto",
        params={"persona_id": esterno["persona_id"]},
    )
    assert response.status_code == 200
    pages = pdf_pages_text(response.content)
    assert len(pages) == 1
    assert "MARCIA_TROMBA" in pages[0]
