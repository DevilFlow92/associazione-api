from __future__ import annotations

from pydantic import BaseModel

from app.schemas._types import TzNaiveDatetime
from app.schemas.servizio import IndirizzoInServizio


class ServizioInProva(BaseModel):
    id: int
    descrizione_servizio: str
    data_servizio: TzNaiveDatetime

    model_config = {"from_attributes": True}


class ProvaBase(BaseModel):
    banda_codice: int
    data_prova: TzNaiveDatetime
    indirizzo_id: int | None = None
    servizio_id: int | None = None
    note: str | None = None


class ProvaCreate(ProvaBase):
    pass


class ProvaUpdate(BaseModel):
    banda_codice: int | None = None
    data_prova: TzNaiveDatetime | None = None
    indirizzo_id: int | None = None
    servizio_id: int | None = None
    note: str | None = None


class ProvaResponse(ProvaBase):
    id: int
    indirizzo: IndirizzoInServizio | None = None
    servizio: ServizioInProva | None = None

    model_config = {"from_attributes": True}
