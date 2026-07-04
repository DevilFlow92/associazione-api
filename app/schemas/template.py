from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    nome: str
    descrizione: str | None = None
    contenuto_json: dict[str, Any]
    entita_richieste: list[str] = []


class TemplateGenerateRequest(BaseModel):
    entities: dict[str, int]


class TemplateUpdate(BaseModel):
    nome: str | None = None
    descrizione: str | None = None
    contenuto_json: dict[str, Any] | None = None
    entita_richieste: list[str] | None = None


class TemplateResponse(BaseModel):
    id: int
    nome: str
    descrizione: str | None
    contenuto_json: dict[str, Any]
    entita_richieste: list[str]
    creato_il: datetime
    aggiornato_il: datetime

    model_config = {"from_attributes": True}
