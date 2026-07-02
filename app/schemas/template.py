from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    documento_id: int
    nome: str
    descrizione: str | None = None


class TemplateUpdate(BaseModel):
    nome: str | None = None
    descrizione: str | None = None


class DocumentoInTemplate(BaseModel):
    id: int
    nome: str
    mime_type: str
    dimensione_bytes: int

    model_config = {"from_attributes": True}


class TemplateResponse(BaseModel):
    id: int
    documento_id: int
    nome: str
    descrizione: str | None
    creato_il: datetime
    aggiornato_il: datetime
    documento: DocumentoInTemplate | None = None

    model_config = {"from_attributes": True}
