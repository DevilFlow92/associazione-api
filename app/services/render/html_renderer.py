from __future__ import annotations

from html import escape

from app.exceptions.template import TemplateRenderError
from app.services.render.docx_walker import _resolve_mergefield

_HEADING_TAGS = {1: "h1", 2: "h2", 3: "h3"}

_STYLE = """
    @page { size: A4; margin: 2cm; }
    html, body {
        font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
"""


def build_html(contenuto_json: dict, context: dict) -> str:
    """Cammina lo stesso albero ProseMirror/TipTap del docx_walker e produce HTML."""
    if contenuto_json.get("type") != "doc":
        raise TemplateRenderError(
            "Il contenuto del template deve avere type 'doc' come radice"
        )

    body = "".join(
        _render_block(node, context) for node in contenuto_json.get("content", [])
    )

    return (
        "<!DOCTYPE html>"
        '<html><head><meta charset="utf-8">'
        f"<style>{_STYLE}</style>"
        f"</head><body>{body}</body></html>"
    )


def _render_block(node: dict, context: dict) -> str:
    node_type = node.get("type")
    if node_type == "paragraph":
        inner = _render_inline_content(node.get("content", []), context)
        return f"<p>{inner}</p>"
    elif node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        tag = _HEADING_TAGS.get(level, "h1")
        inner = _render_inline_content(node.get("content", []), context)
        return f"<{tag}>{inner}</{tag}>"
    else:
        raise TemplateRenderError(f"Tipo di nodo non supportato: {node_type!r}")


def _render_inline_content(nodes: list[dict], context: dict) -> str:
    return "".join(_render_inline(node, context) for node in nodes)


def _render_inline(node: dict, context: dict) -> str:
    node_type = node.get("type")
    if node_type == "text":
        return _wrap_marks(escape(node.get("text", "")), node.get("marks", []))
    elif node_type == "mergefield":
        chiave = node["attrs"]["chiave"]
        valore = _resolve_mergefield(chiave, context)
        return _wrap_marks(escape(valore), node.get("marks", []))
    else:
        raise TemplateRenderError(f"Tipo di nodo inline non supportato: {node_type!r}")


def _wrap_marks(text: str, marks: list[dict]) -> str:
    for mark in marks:
        mark_type = mark.get("type")
        if mark_type == "bold":
            text = f"<strong>{text}</strong>"
        elif mark_type == "italic":
            text = f"<em>{text}</em>"
    return text
