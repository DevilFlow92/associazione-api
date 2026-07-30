from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class CorsoInIscrizioneCorso(BaseModel):
    id: int
    anno: int

    model_config = {"from_attributes": True}


class PersonaInIscrizioneCorso(BaseModel):
    id: int
    nome: str | None = None
    cognome: str | None = None

    model_config = {"from_attributes": True}


class StatoIscrizioneCorsoNested(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class DocumentoInIscrizioneCorso(BaseModel):
    id: int
    nome: str
    mime_type: str

    model_config = {"from_attributes": True}


class IscrizioneCorsoBase(BaseModel):
    corso_id: int
    persona_id: int
    stato_iscrizione_corso_codice: int
    documento_id: int | None = None
    data_iscrizione: date
    note: str | None = None


class IscrizioneCorsoCreate(IscrizioneCorsoBase):
    pass


class IscrizioneCorsoUpdate(BaseModel):
    corso_id: int | None = None
    persona_id: int | None = None
    stato_iscrizione_corso_codice: int | None = None
    documento_id: int | None = None
    data_iscrizione: date | None = None
    note: str | None = None


class IscrizioneCorsoResponse(IscrizioneCorsoBase):
    id: int
    corso: CorsoInIscrizioneCorso
    persona: PersonaInIscrizioneCorso
    stato_iscrizione_corso: StatoIscrizioneCorsoNested
    documento: DocumentoInIscrizioneCorso | None = None

    model_config = {"from_attributes": True}
