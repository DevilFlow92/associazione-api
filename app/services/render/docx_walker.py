from __future__ import annotations

import io
from typing import Any

from docx import Document as DocxDocument
from docx.text.paragraph import Paragraph

from app.exceptions.template import TemplateRenderError

_HEADING_STYLES = {1: "Heading 1", 2: "Heading 2", 3: "Heading 3"}


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
    if node_type == "paragraph":
        paragraph = doc.add_paragraph()
        _add_inline_content(paragraph, node.get("content", []), context)
    elif node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        paragraph = doc.add_paragraph(style=_HEADING_STYLES.get(level, "Heading 1"))
        _add_inline_content(paragraph, node.get("content", []), context)
    else:
        raise TemplateRenderError(f"Tipo di nodo non supportato: {node_type!r}")


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


def _resolve_mergefield(chiave: str, context: dict) -> str:
    entita, _, campo = chiave.partition(".")
    valori = context.get(entita)
    if not valori or campo not in valori or valori[campo] is None:
        return f"[campo mancante: {chiave}]"
    return str(valori[campo])
