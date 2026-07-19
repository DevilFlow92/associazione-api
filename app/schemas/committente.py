from __future__ import annotations

from pydantic import BaseModel


class ProvinciaInCommittente(BaseModel):
    codice: int
    sigla: str | None = None

    model_config = {"from_attributes": True}


class ComuneInCommittente(BaseModel):
    codice: int
    descrizione: str
    provincia: ProvinciaInCommittente | None = None

    model_config = {"from_attributes": True}


class IndirizzoInCommittente(BaseModel):
    id: int
    prima_riga: str | None = None
    numero_civico: str | None = None
    cap: str | None = None
    comune: ComuneInCommittente | None = None

    model_config = {"from_attributes": True}


class CommittenteBase(BaseModel):
    denominazione: str
    indirizzo_id: int | None = None
    codice_fiscale_piva: str | None = None
    note: str | None = None


class CommittenteCreate(CommittenteBase):
    pass


class CommittenteUpdate(BaseModel):
    denominazione: str | None = None
    indirizzo_id: int | None = None
    codice_fiscale_piva: str | None = None
    note: str | None = None


class CommittenteResponse(CommittenteBase):
    id: int
    indirizzo: IndirizzoInCommittente | None = None

    model_config = {"from_attributes": True}
