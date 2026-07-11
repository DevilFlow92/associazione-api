from __future__ import annotations

import io
from typing import Any

from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor
from docx.text.paragraph import Paragraph

from app.exceptions.template import TemplateRenderError
from app.services.render.fonts import sanitize_font_family, validate_hex_color

_HEADING_STYLES = {1: "Heading 1", 2: "Heading 2", 3: "Heading 3"}

# Schema ProseMirror/TipTap supportato (deve restare sincronizzato con
# html_renderer.py):
# - nodi blocco: doc, paragraph, heading (attrs.level 1-3)
#   - attrs.textAlign su paragraph/heading: left | center | right | justify
#     (default "left" se assente)
# - nodi inline: text, mergefield (attrs.chiave)
# - marks su text/mergefield: bold, italic,
#   textStyle (attrs.color "#RRGGBB", attrs.fontFamily — solo se in
#   app.services.render.fonts.SAFE_FONTS, altrimenti ignorato)
_TEXT_ALIGN = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def build_docx(contenuto_json: dict, context: dict) -> bytes:
    """Cammina l'albero ProseMirror/TipTap del template e produce un .docx."""
    if contenuto_json.get("type") != "doc":
        raise TemplateRenderError(
            "Il contenuto del template deve avere type 'doc' come radice"
        )

    doc = DocxDocument()
    for node in contenuto_json.get("content", []):
        _add_block(doc, node, context)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _add_block(doc: Any, node: dict, context: dict) -> None:
    node_type = node.get("type")
    attrs = node.get("attrs", {})
    if node_type == "paragraph":
        paragraph = doc.add_paragraph()
        _apply_text_align(paragraph, attrs.get("textAlign"))
        _add_inline_content(paragraph, node.get("content", []), context)
    elif node_type == "heading":
        level = attrs.get("level", 1)
        paragraph = doc.add_paragraph(style=_HEADING_STYLES.get(level, "Heading 1"))
        _apply_text_align(paragraph, attrs.get("textAlign"))
        _add_inline_content(paragraph, node.get("content", []), context)
    else:
        raise TemplateRenderError(f"Tipo di nodo non supportato: {node_type!r}")


def _apply_text_align(paragraph: Paragraph, text_align: str | None) -> None:
    # Se assente (o non riconosciuto) lascia l'allineamento invariato (None),
    # così i template preesistenti senza textAlign producono lo stesso .docx
    # di prima — WD_ALIGN_PARAGRAPH.LEFT lo imposterebbe esplicitamente,
    # cambiando l'XML generato anche se visivamente equivalente.
    if text_align in _TEXT_ALIGN and text_align != "left":
        paragraph.alignment = _TEXT_ALIGN[text_align]


def _add_inline_content(paragraph: Paragraph, nodes: list[dict], context: dict) -> None:
    for node in nodes:
        node_type = node.get("type")
        if node_type == "text":
            _add_run(paragraph, node.get("text", ""), node.get("marks", []))
        elif node_type == "mergefield":
            chiave = node["attrs"]["chiave"]
            _add_run(
                paragraph, _resolve_mergefield(chiave, context), node.get("marks", [])
            )
        else:
            raise TemplateRenderError(
                f"Tipo di nodo inline non supportato: {node_type!r}"
            )


def _add_run(paragraph: Paragraph, text: str, marks: list[dict]) -> None:
    run = paragraph.add_run(text)
    for mark in marks:
        mark_type = mark.get("type")
        if mark_type == "bold":
            run.bold = True
        elif mark_type == "italic":
            run.italic = True
        elif mark_type == "textStyle":
            _apply_text_style(run, mark.get("attrs", {}))


def _apply_text_style(run: Any, attrs: dict) -> None:
    hex_color = validate_hex_color(attrs.get("color"))
    if hex_color:
        run.font.color.rgb = RGBColor.from_string(hex_color)

    font_family = sanitize_font_family(attrs.get("fontFamily"))
    if font_family:
        run.font.name = font_family


def _resolve_mergefield(chiave: str, context: dict) -> str:
    entita, _, campo = chiave.partition(".")
    valori = context.get(entita)
    if not valori or campo not in valori or valori[campo] is None:
        return f"[campo mancante: {chiave}]"
    return str(valori[campo])
