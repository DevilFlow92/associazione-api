from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class StrumentoInEsterno(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class PersonaInEsterno(BaseModel):
    id: int
    nome: str | None = None
    cognome: str | None = None
    codice_fiscale: str | None = None
    data_nascita: date | None = None

    model_config = {"from_attributes": True}


class EsternoBase(BaseModel):
    strumento_codice: int
    attivo: bool = True


class EsternoCreate(EsternoBase):
    persona_id: int


class EsternoUpdate(BaseModel):
    codice_esterno: str | None = Field(default=None, max_length=5)
    strumento_codice: int | None = None
    attivo: bool | None = None


class EsternoResponse(EsternoBase):
    id: int
    persona_id: int
    codice_esterno: str
    strumento: StrumentoInEsterno | None = None
    persona: PersonaInEsterno | None = None

    model_config = {"from_attributes": True}
