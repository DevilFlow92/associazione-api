from __future__ import annotations

import io

import pytest
from docx import Document as DocxDocument
from httpx import AsyncClient

from app.exceptions.template import TemplateRenderError
from app.services.render.docx_walker import build_docx


def _read_paragraphs(content: bytes) -> list[str]:
    doc = DocxDocument(io.BytesIO(content))
    return [p.text for p in doc.paragraphs]


def test_build_docx_paragraph_and_heading():
    contenuto = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Titolo"}],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Testo semplice"}],
            },
        ],
    }
    content = build_docx(contenuto, {})
    assert _read_paragraphs(content) == ["Titolo", "Testo semplice"]


def test_build_docx_bold_and_italic_marks():
    contenuto = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "grassetto",
                        "marks": [{"type": "bold"}],
                    },
                    {"type": "text", "text": " e "},
                    {
                        "type": "text",
                        "text": "corsivo",
                        "marks": [{"type": "italic"}],
                    },
                ],
            }
        ],
    }
    content = build_docx(contenuto, {})
    doc = DocxDocument(io.BytesIO(content))
    runs = doc.paragraphs[0].runs
    assert runs[0].text == "grassetto"
    assert runs[0].bold is True
    assert runs[1].text == " e "
    assert not runs[1].bold
    assert runs[2].text == "corsivo"
    assert runs[2].italic is True


def test_build_docx_mergefield_resolved():
    contenuto = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Gentile "},
                    {
                        "type": "mergefield",
                        "attrs": {"chiave": "socio.nome"},
                    },
                ],
            }
        ],
    }
    content = build_docx(contenuto, {"socio": {"nome": "Mario"}})
    assert _read_paragraphs(content) == ["Gentile Mario"]


def test_build_docx_mergefield_non_risolvibile():
    contenuto = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "mergefield",
                        "attrs": {"chiave": "socio.nome"},
                    }
                ],
            }
        ],
    }
    content = build_docx(contenuto, {})
    assert _read_paragraphs(content) == ["[campo mancante: socio.nome]"]


def test_build_docx_tipo_nodo_non_supportato():
    contenuto = {"type": "doc", "content": [{"type": "table", "content": []}]}
    with pytest.raises(TemplateRenderError):
        build_docx(contenuto, {})


async def _create_persona(ac: AsyncClient) -> dict:
    resp = await ac.post(
        "/api/v1/persone/",
        json={
            "banda_codice": 1,
            "nome": "Mario",
            "cognome": "Rossi",
            "codice_fiscale": "RSSMRA80A01H501U",
            "data_nascita": "1980-01-01",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_generate_endpoint_produce_docx_valido(client: AsyncClient):
    persona = await _create_persona(client)
    socio_resp = await client.post(
        "/api/v1/soci/",
        json={
            "persona_id": persona["id"],
            "codice_socio": "S001",
            "ruolo_banda_codice": 10,
        },
    )
    assert socio_resp.status_code == 201, socio_resp.text
    socio_id = socio_resp.json()["id"]

    template_resp = await client.post(
        "/api/v1/templates/",
        json={
            "nome": "Modulo Iscrizione",
            "contenuto_json": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Gentile "},
                            {
                                "type": "mergefield",
                                "attrs": {"chiave": "socio.nome"},
                            },
                            {"type": "text", "text": ", con la presente..."},
                        ],
                    }
                ],
            },
            "entita_richieste": ["socio"],
        },
    )
    assert template_resp.status_code == 201, template_resp.text
    template_id = template_resp.json()["id"]

    generate_resp = await client.post(
        f"/api/v1/templates/{template_id}/generate",
        json={"entities": {"socio": socio_id}},
    )
    assert generate_resp.status_code == 200, generate_resp.text
    documento = generate_resp.json()
    assert documento["mime_type"] == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    download_resp = await client.get(f"/api/v1/documenti/{documento['id']}/download")
    assert download_resp.status_code == 200
    doc = DocxDocument(io.BytesIO(download_resp.content))
    assert doc.paragraphs[0].text == "Gentile Mario, con la presente..."


@pytest.mark.asyncio
async def test_generate_endpoint_forbidden_senza_permesso(client: AsyncClient):
    from app.api.deps import get_current_user
    from app.models.utente import TipoUtente, Utente
    from main import app

    def _user_senza_permessi() -> Utente:
        return Utente(id=1, tipo=TipoUtente.UMANO, email="test@example.com")

    app.dependency_overrides[get_current_user] = _user_senza_permessi
    response = await client.post("/api/v1/templates/1/generate", json={"entities": {}})
    assert response.status_code == 403
