from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class PersonaBase(BaseModel):
    banda_codice: int
    cognome: str | None = None
    nome: str | None = None
    ragione_sociale: str | None = None
    comune_nascita_codice: int | None = None
    data_nascita: date | None = None
    codice_fiscale: str | None = None


class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(BaseModel):
    banda_codice: int | None = None
    cognome: str | None = None
    nome: str | None = None
    ragione_sociale: str | None = None
    comune_nascita_codice: int | None = None
    data_nascita: date | None = None
    codice_fiscale: str | None = None


class PersonaResponse(PersonaBase):
    id: int

    model_config = {"from_attributes": True}
