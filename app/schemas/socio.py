from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ComuneInSocio(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class RuoloBandaInSocio(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class StrumentoInSocio(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class PersonaInSocio(BaseModel):
    id: int
    nome: str | None = None
    cognome: str | None = None
    codice_fiscale: str | None = None
    data_nascita: date | None = None
    comune_nascita_codice: int | None = None
    comune_nascita: ComuneInSocio | None = None

    model_config = {"from_attributes": True}


class SocioBase(BaseModel):
    codice_socio: str
    banda_codice: int
    ruolo_banda_codice: int
    strumento_codice: int | None = None


class SocioCreate(SocioBase):
    persona_id: int


class SocioUpdate(BaseModel):
    codice_socio: str | None = None
    banda_codice: int | None = None
    ruolo_banda_codice: int | None = None
    strumento_codice: int | None = None


class SocioResponse(SocioBase):
    id: int
    persona_id: int
    persona: PersonaInSocio | None = None
    ruolo_banda: RuoloBandaInSocio | None = None
    strumento: StrumentoInSocio | None = None

    model_config = {"from_attributes": True}
