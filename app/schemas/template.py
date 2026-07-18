from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    nome: str
    descrizione: str | None = None
    contenuto_json: dict[str, Any]
    entita_richieste: list[str] = []
    sotto_cartella_id: int | None = None


class TemplateGenerateRequest(BaseModel):
    entities: dict[str, int]
    nome_file: str | None = None


class TemplatePreviewRequest(BaseModel):
    contenuto_json: dict[str, Any]
    entities: dict[str, int]


class TemplateUpdate(BaseModel):
    nome: str | None = None
    descrizione: str | None = None
    contenuto_json: dict[str, Any] | None = None
    entita_richieste: list[str] | None = None
    sotto_cartella_id: int | None = None


class TemplateResponse(BaseModel):
    id: int
    nome: str
    descrizione: str | None
    contenuto_json: dict[str, Any]
    entita_richieste: list[str]
    sotto_cartella_id: int | None
    creato_il: datetime
    aggiornato_il: datetime

    model_config = {"from_attributes": True}
