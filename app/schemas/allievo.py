from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PersonaInAllievo(BaseModel):
    id: int
    nome: str | None = None
    cognome: str | None = None
    codice_fiscale: str | None = None
    data_nascita: date | None = None

    model_config = {"from_attributes": True}


class IndirizzoInAllievo(BaseModel):
    id: int
    prima_riga: str | None = None
    seconda_riga: str | None = None
    cap: str | None = None
    numero_civico: str | None = None

    model_config = {"from_attributes": True}


class AllievoBase(BaseModel):
    indirizzo_id: int | None = None


class AllievoCreate(AllievoBase):
    persona_id: int


class AllievoUpdate(BaseModel):
    codice_allievo: str | None = Field(default=None, max_length=5)
    indirizzo_id: int | None = None


class AllievoResponse(AllievoBase):
    id: int
    persona_id: int
    codice_allievo: str
    indirizzo: IndirizzoInAllievo | None = None
    persona: PersonaInAllievo | None = None

    model_config = {"from_attributes": True}
