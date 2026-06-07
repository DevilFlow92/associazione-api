from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.template import TipoTemplate


class TemplateResponse(BaseModel):
    id: int
    nome: str
    tipo: TipoTemplate
    descrizione: str | None
    file_path: str
    mime_type: str
    dimensione_bytes: int
    checksum: str
    attivo: bool
    creato_il: datetime
    aggiornato_il: datetime

    model_config = {"from_attributes": True}


class TemplateUpdate(BaseModel):
    nome: str | None = None
    descrizione: str | None = None
    attivo: bool | None = None
