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


class TemplateResponse(BaseModel):
    id: int
    documento_id: int
    nome: str
    descrizione: str | None
    creato_il: datetime
    aggiornato_il: datetime

    model_config = {"from_attributes": True}
