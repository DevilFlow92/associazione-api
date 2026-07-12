from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImageAsset:
    """Contenuto binario e mime_type di un Documento referenziato da un nodo
    "image" del template, già risolto prima della resa (vedi
    TemplateService._load_images)."""

    content: bytes
    mime_type: str
