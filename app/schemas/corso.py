from __future__ import annotations

from pydantic import BaseModel


class TipoCorsoInCorso(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class PersonaInCorso(BaseModel):
    id: int
    nome: str
    cognome: str

    model_config = {"from_attributes": True}


class CorsoBase(BaseModel):
    banda_codice: int
    tipo_corso_codice: int
    anno: int
    coordinatore_persona_id: int | None = None
    insegnante_persona_id: int | None = None
    note: str | None = None


class CorsoCreate(CorsoBase):
    pass


class CorsoUpdate(BaseModel):
    banda_codice: int | None = None
    tipo_corso_codice: int | None = None
    anno: int | None = None
    coordinatore_persona_id: int | None = None
    insegnante_persona_id: int | None = None
    note: str | None = None


class CorsoResponse(CorsoBase):
    id: int
    tipo_corso: TipoCorsoInCorso
    coordinatore: PersonaInCorso | None = None
    insegnante: PersonaInCorso | None = None

    model_config = {"from_attributes": True}
