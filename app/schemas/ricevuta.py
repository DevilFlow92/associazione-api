from __future__ import annotations

from pydantic import BaseModel

from app.schemas._types import TzNaiveDatetime


class PersonaInRicevuta(BaseModel):
    id: int
    nome: str | None = None
    cognome: str | None = None

    model_config = {"from_attributes": True}


class EsternoInRicevuta(BaseModel):
    id: int
    codice_esterno: str
    persona: PersonaInRicevuta | None = None

    model_config = {"from_attributes": True}


class RicevutaBase(BaseModel):
    data_ricevuta: TzNaiveDatetime
    importo: float
    note_in_stampa: str | None = None
    note_fuori_stampa: str | None = None


class RicevutaCreate(RicevutaBase):
    servizio_id: int | None = None
    esterno_id: int | None = None
    documento_id: int | None = None


class RicevutaUpdate(BaseModel):
    data_ricevuta: TzNaiveDatetime | None = None
    importo: float | None = None
    note_in_stampa: str | None = None
    note_fuori_stampa: str | None = None
    servizio_id: int | None = None
    esterno_id: int | None = None
    documento_id: int | None = None


class RicevutaResponse(RicevutaBase):
    id: int
    servizio_id: int | None
    esterno_id: int | None
    documento_id: int | None
    esterno: EsternoInRicevuta | None = None

    model_config = {"from_attributes": True}
