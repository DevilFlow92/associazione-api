from __future__ import annotations

from pydantic import BaseModel

from app.schemas._types import TzNaiveDatetime


class ProvinciaInServizio(BaseModel):
    codice: int
    sigla: str | None = None

    model_config = {"from_attributes": True}


class ComuneInServizio(BaseModel):
    codice: int
    descrizione: str
    provincia: ProvinciaInServizio | None = None

    model_config = {"from_attributes": True}


class IndirizzoInServizio(BaseModel):
    id: int
    prima_riga: str | None = None
    numero_civico: str | None = None
    cap: str | None = None
    comune: ComuneInServizio | None = None

    model_config = {"from_attributes": True}


class ServizioBase(BaseModel):
    banda_codice: int
    anno: int
    descrizione_servizio: str
    data_servizio: TzNaiveDatetime
    indirizzo_id: int
    note: str | None = None


class ServizioCreate(ServizioBase):
    pass


class ServizioUpdate(BaseModel):
    banda_codice: int | None = None
    anno: int | None = None
    descrizione_servizio: str | None = None
    data_servizio: TzNaiveDatetime | None = None
    indirizzo_id: int | None = None
    note: str | None = None


class ServizioResponse(ServizioBase):
    id: int
    indirizzo: IndirizzoInServizio | None = None

    model_config = {"from_attributes": True}
