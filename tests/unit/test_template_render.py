from __future__ import annotations

import io
import time

import pytest
from docx import Document as DocxDocument
from httpx import AsyncClient

from app.exceptions.template import TemplateRenderError
from app.services.render.docx_walker import build_docx
from app.services.render.html_renderer import build_html
from app.services.render.pdf_renderer import build_pdf


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


def test_build_html_risolve_mergefield_e_marks():
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
                "content": [
                    {"type": "text", "text": "Gentile "},
                    {"type": "mergefield", "attrs": {"chiave": "socio.nome"}},
                    {
                        "type": "text",
                        "text": " grassetto",
                        "marks": [{"type": "bold"}],
                    },
                ],
            },
        ],
    }
    html = build_html(contenuto, {"socio": {"nome": "Mario"}})
    assert "<h1>Titolo</h1>" in html
    assert "Gentile Mario" in html
    assert "<strong> grassetto</strong>" in html
    assert "@page { size: A4; margin: 2cm; }" in html
    assert "unpkg.com" not in html
    assert "http" not in html


def test_build_html_mergefield_non_risolvibile():
    contenuto = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "mergefield", "attrs": {"chiave": "socio.nome"}}],
            }
        ],
    }
    html = build_html(contenuto, {})
    assert "[campo mancante: socio.nome]" in html


def test_build_html_tipo_nodo_non_supportato():
    contenuto = {"type": "doc", "content": [{"type": "table", "content": []}]}
    with pytest.raises(TemplateRenderError):
        build_html(contenuto, {})


def _paragrafo_con_align(text_align: str | None) -> dict:
    attrs = {} if text_align is None else {"textAlign": text_align}
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "attrs": attrs,
                "content": [{"type": "text", "text": "Testo"}],
            }
        ],
    }


@pytest.mark.parametrize(
    "text_align,expected",
    [("center", 1), ("right", 2), ("justify", 3)],
)
def test_build_docx_text_align(text_align, expected):
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    content = build_docx(_paragrafo_con_align(text_align), {})
    doc = DocxDocument(io.BytesIO(content))
    assert doc.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH(expected)


@pytest.mark.parametrize("text_align", ["center", "right", "justify"])
def test_build_html_text_align(text_align):
    html = build_html(_paragrafo_con_align(text_align), {})
    assert f'style="text-align: {text_align};"' in html


def test_build_docx_heading_text_align():
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    contenuto = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1, "textAlign": "center"},
                "content": [{"type": "text", "text": "Titolo"}],
            }
        ],
    }
    content = build_docx(contenuto, {})
    doc = DocxDocument(io.BytesIO(content))
    assert doc.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.CENTER


def test_build_html_heading_text_align():
    contenuto = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1, "textAlign": "right"},
                "content": [{"type": "text", "text": "Titolo"}],
            }
        ],
    }
    html = build_html(contenuto, {})
    assert '<h1 style="text-align: right;">Titolo</h1>' in html


def _paragrafo_con_text_style(attrs: dict) -> dict:
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Colorato",
                        "marks": [{"type": "textStyle", "attrs": attrs}],
                    }
                ],
            }
        ],
    }


def test_build_docx_text_style_color_e_font():
    from docx.shared import RGBColor

    contenuto = _paragrafo_con_text_style({"color": "#FF0000", "fontFamily": "Arial"})
    content = build_docx(contenuto, {})
    doc = DocxDocument(io.BytesIO(content))
    run = doc.paragraphs[0].runs[0]
    assert run.font.color.rgb == RGBColor.from_string("FF0000")
    assert run.font.name == "Arial"


def test_build_html_text_style_color_e_font():
    contenuto = _paragrafo_con_text_style({"color": "#FF0000", "fontFamily": "Arial"})
    html = build_html(contenuto, {})
    assert '<span style="color: #FF0000; font-family: Arial;">Colorato</span>' in html


def test_build_html_text_style_solo_color():
    contenuto = _paragrafo_con_text_style({"color": "#00FF00"})
    html = build_html(contenuto, {})
    assert '<span style="color: #00FF00;">Colorato</span>' in html


def test_build_docx_text_style_font_non_whitelisted_ignorato():
    contenuto = _paragrafo_con_text_style({"fontFamily": "ComicSansMS"})
    content = build_docx(contenuto, {})
    doc = DocxDocument(io.BytesIO(content))
    run = doc.paragraphs[0].runs[0]
    assert run.font.name is None


def test_build_html_text_style_font_non_whitelisted_ignorato():
    contenuto = _paragrafo_con_text_style({"fontFamily": "ComicSansMS"})
    html = build_html(contenuto, {})
    assert "ComicSansMS" not in html
    assert "<span" not in html


def test_build_docx_senza_textalign_ne_textstyle_nessuna_regressione():
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
                "content": [
                    {"type": "text", "text": "grassetto", "marks": [{"type": "bold"}]}
                ],
            },
        ],
    }
    content = build_docx(contenuto, {})
    doc = DocxDocument(io.BytesIO(content))
    assert doc.paragraphs[0].alignment is None
    assert doc.paragraphs[1].alignment is None
    assert doc.paragraphs[1].runs[0].bold is True


def test_build_html_senza_textalign_ne_textstyle_nessuna_regressione():
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
                "content": [
                    {"type": "text", "text": "grassetto", "marks": [{"type": "bold"}]}
                ],
            },
        ],
    }
    html = build_html(contenuto, {})
    assert "<h1>Titolo</h1>" in html
    assert "<p><strong>grassetto</strong></p>" in html
    assert "style=" not in html


@pytest.mark.parametrize("colore_malformato", ["notacolor", "#fff", "12345", ""])
def test_build_docx_text_style_colore_malformato_ignorato(colore_malformato):
    contenuto = _paragrafo_con_text_style({"color": colore_malformato})
    content = build_docx(contenuto, {})
    doc = DocxDocument(io.BytesIO(content))
    run = doc.paragraphs[0].runs[0]
    assert run.font.color.rgb is None


@pytest.mark.parametrize("colore_malformato", ["notacolor", "#fff", "12345", ""])
def test_build_html_text_style_colore_malformato_ignorato(colore_malformato):
    contenuto = _paragrafo_con_text_style({"color": colore_malformato})
    html = build_html(contenuto, {})
    assert "color:" not in html
    assert "<span" not in html or "font-family:" in html


def test_build_docx_text_style_colore_valido_con_e_senza_hash():
    for colore in ["#FF0000", "FF0000"]:
        contenuto = _paragrafo_con_text_style({"color": colore})
        content = build_docx(contenuto, {})
        doc = DocxDocument(io.BytesIO(content))
        run = doc.paragraphs[0].runs[0]
        from docx.shared import RGBColor

        assert run.font.color.rgb == RGBColor.from_string("FF0000")


def test_build_html_text_style_colore_valido_con_e_senza_hash():
    for colore in ["#FF0000", "FF0000"]:
        contenuto = _paragrafo_con_text_style({"color": colore})
        html = build_html(contenuto, {})
        assert "color: #FF0000" in html


def _contenuto_multi_pagina() -> dict:
    testo_lungo = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20
    paragrafi = [
        {"type": "paragraph", "content": [{"type": "text", "text": testo_lungo}]}
        for _ in range(80)
    ]
    return {"type": "doc", "content": paragrafi}


@pytest.mark.asyncio
async def test_build_pdf_produce_pdf_valido():
    html = build_html(_contenuto_multi_pagina(), {})

    inizio = time.monotonic()
    content = await build_pdf(html)
    durata = time.monotonic() - inizio

    assert content[:5] == b"%PDF-"
    # Se l'attesa di impaginazione degrada di nuovo a un timeout fisso
    # (invece di risolversi sul completamento reale di paged.js), questo
    # test tornerebbe a durare ~10s+: un tempo basso è la prova che
    # l'hook PagedConfig.after ha davvero segnalato il completamento.
    assert durata < 5, (
        f"build_pdf ha impiegato {durata:.1f}s: l'attesa sembra basarsi "
        "su un timeout invece che sul completamento reale di paged.js"
    )


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


async def _create_socio_con_template(client: AsyncClient) -> tuple[int, int]:
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
    return template_resp.json()["id"], socio_id


@pytest.mark.asyncio
async def test_generate_docx_endpoint_produce_docx_valido(client: AsyncClient):
    template_id, socio_id = await _create_socio_con_template(client)

    generate_resp = await client.post(
        f"/api/v1/templates/{template_id}/generate/docx",
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
async def test_generate_pdf_endpoint_produce_pdf_valido(client: AsyncClient):
    template_id, socio_id = await _create_socio_con_template(client)

    generate_resp = await client.post(
        f"/api/v1/templates/{template_id}/generate/pdf",
        json={"entities": {"socio": socio_id}},
    )
    assert generate_resp.status_code == 200, generate_resp.text
    documento = generate_resp.json()
    assert documento["mime_type"] == "application/pdf"

    download_resp = await client.get(f"/api/v1/documenti/{documento['id']}/download")
    assert download_resp.status_code == 200
    assert download_resp.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_preview_endpoint_risolve_mergefield(client: AsyncClient):
    template_id, socio_id = await _create_socio_con_template(client)

    resp = await client.post(
        f"/api/v1/templates/{template_id}/preview",
        json={
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
                        ],
                    }
                ],
            },
            "entities": {"socio": socio_id},
        },
    )
    assert resp.status_code == 200, resp.text
    assert "Gentile Mario" in resp.json()["html"]


@pytest.mark.asyncio
async def test_preview_endpoint_usa_contenuto_del_body_non_quello_salvato(
    client: AsyncClient,
):
    template_id, socio_id = await _create_socio_con_template(client)

    resp = await client.post(
        f"/api/v1/templates/{template_id}/preview",
        json={
            "contenuto_json": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Contenuto non salvato"}],
                    }
                ],
            },
            "entities": {"socio": socio_id},
        },
    )
    assert resp.status_code == 200, resp.text
    html = resp.json()["html"]
    assert "Contenuto non salvato" in html
    assert "con la presente" not in html


@pytest.mark.asyncio
async def test_preview_endpoint_404_template_inesistente(client: AsyncClient):
    resp = await client.post(
        "/api/v1/templates/999999/preview",
        json={
            "contenuto_json": {"type": "doc", "content": []},
            "entities": {},
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_preview_endpoint_forbidden_senza_permesso(client: AsyncClient):
    from app.api.deps import get_current_user
    from app.models.utente import TipoUtente, Utente
    from main import app

    def _user_senza_permessi() -> Utente:
        return Utente(id=1, tipo=TipoUtente.UMANO, email="test@example.com")

    app.dependency_overrides[get_current_user] = _user_senza_permessi
    response = await client.post(
        "/api/v1/templates/1/preview",
        json={"contenuto_json": {"type": "doc", "content": []}, "entities": {}},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_generate_docx_endpoint_forbidden_senza_permesso(client: AsyncClient):
    from app.api.deps import get_current_user
    from app.models.utente import TipoUtente, Utente
    from main import app

    def _user_senza_permessi() -> Utente:
        return Utente(id=1, tipo=TipoUtente.UMANO, email="test@example.com")

    app.dependency_overrides[get_current_user] = _user_senza_permessi
    response = await client.post(
        "/api/v1/templates/1/generate/docx", json={"entities": {}}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_generate_pdf_endpoint_forbidden_senza_permesso(client: AsyncClient):
    from app.api.deps import get_current_user
    from app.models.utente import TipoUtente, Utente
    from main import app

    def _user_senza_permessi() -> Utente:
        return Utente(id=1, tipo=TipoUtente.UMANO, email="test@example.com")

    app.dependency_overrides[get_current_user] = _user_senza_permessi
    response = await client.post(
        "/api/v1/templates/1/generate/pdf", json={"entities": {}}
    )
    assert response.status_code == 403
