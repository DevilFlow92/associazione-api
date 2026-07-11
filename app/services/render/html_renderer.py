from __future__ import annotations

from html import escape

from app.exceptions.template import TemplateRenderError
from app.services.render.docx_walker import _resolve_mergefield
from app.services.render.fonts import sanitize_font_family, validate_hex_color

_HEADING_TAGS = {1: "h1", 2: "h2", 3: "h3"}

# Schema ProseMirror/TipTap supportato (deve restare sincronizzato con
# docx_walker.py):
# - nodi blocco: doc, paragraph, heading (attrs.level 1-3),
#   bulletList/orderedList (contengono listItem; orderedList ha
#   attrs.start opzionale), listItem (contiene blocchi, tipicamente
#   paragraph, oppure a sua volta bulletList/orderedList annidate)
#   - attrs.textAlign su paragraph/heading: left | center | right | justify
#     (default "left" se assente)
# - nodi inline: text, mergefield (attrs.chiave)
# - marks su text/mergefield: bold, italic,
#   textStyle (attrs.color "#RRGGBB", attrs.fontFamily — solo se in
#   app.services.render.fonts.SAFE_FONTS, altrimenti ignorato)
# - marcatori di lista "stile Word": il livello di annidamento (0, 1, 2...)
#   determina il list-style-type CSS, riciclando ogni 3 livelli (bulletList:
#   disc/circle/square; orderedList: decimal/lower-alpha/lower-roman).
_VALID_TEXT_ALIGN = {"left", "center", "right", "justify"}
_BULLET_LIST_MARKERS = ["disc", "circle", "square"]
_ORDERED_LIST_MARKERS = ["decimal", "lower-alpha", "lower-roman"]

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
    attrs = node.get("attrs", {})
    if node_type == "paragraph":
        inner = _render_inline_content(node.get("content", []), context)
        return f"<p{_text_align_attr(attrs)}>{inner}</p>"
    elif node_type == "heading":
        level = attrs.get("level", 1)
        tag = _HEADING_TAGS.get(level, "h1")
        inner = _render_inline_content(node.get("content", []), context)
        return f"<{tag}{_text_align_attr(attrs)}>{inner}</{tag}>"
    elif node_type in ("bulletList", "orderedList"):
        return _render_list(node, context, depth=0)
    else:
        raise TemplateRenderError(f"Tipo di nodo non supportato: {node_type!r}")


def _render_list(node: dict, context: dict, depth: int) -> str:
    is_ordered = node.get("type") == "orderedList"
    markers = _ORDERED_LIST_MARKERS if is_ordered else _BULLET_LIST_MARKERS
    marker = markers[depth % len(markers)]
    tag = "ol" if is_ordered else "ul"

    start_attr = ""
    if is_ordered:
        start = node.get("attrs", {}).get("start")
        if start and start != 1:
            start_attr = f' start="{start}"'

    items = "".join(
        _render_list_item(item, context, depth) for item in node.get("content", [])
    )
    return f'<{tag}{start_attr} style="list-style-type: {marker};">{items}</{tag}>'


def _render_list_item(item_node: dict, context: dict, depth: int) -> str:
    inner = "".join(
        _render_list_item_child(child, context, depth)
        for child in item_node.get("content", [])
    )
    return f"<li>{inner}</li>"


def _render_list_item_child(child: dict, context: dict, depth: int) -> str:
    child_type = child.get("type")
    if child_type == "paragraph":
        return _render_block(child, context)
    elif child_type in ("bulletList", "orderedList"):
        return _render_list(child, context, depth + 1)
    else:
        raise TemplateRenderError(
            f"Tipo di nodo non supportato dentro listItem: {child_type!r}"
        )


def _text_align_attr(attrs: dict) -> str:
    text_align = attrs.get("textAlign")
    if text_align not in _VALID_TEXT_ALIGN or text_align == "left":
        return ""
    return f' style="text-align: {text_align};"'


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
        elif mark_type == "textStyle":
            text = _wrap_text_style(text, mark.get("attrs", {}))
    return text


def _wrap_text_style(text: str, attrs: dict) -> str:
    declarations = []

    hex_color = validate_hex_color(attrs.get("color"))
    if hex_color:
        declarations.append(f"color: #{hex_color}")

    font_family = sanitize_font_family(attrs.get("fontFamily"))
    if font_family:
        declarations.append(f"font-family: {font_family}")

    if not declarations:
        return text
    return f'<span style="{"; ".join(declarations)};">{text}</span>'
