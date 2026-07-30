from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.models.ricevuta import TipoRicevuta
from app.schemas._types import TzNaiveDatetime


class RicevutaInPagamentoCorso(BaseModel):
    id: int
    data_ricevuta: TzNaiveDatetime
    importo: float
    tipo_ricevuta: TipoRicevuta | None = None
    persona_id: int | None = None

    model_config = {"from_attributes": True}


class PagamentoCorsoBase(BaseModel):
    iscrizione_corso_id: int
    data_pagamento: date
    importo: float
    note: str | None = None


class PagamentoCorsoCreate(PagamentoCorsoBase):
    pass


class PagamentoCorsoUpdate(BaseModel):
    data_pagamento: date | None = None
    importo: float | None = None
    note: str | None = None


class PagamentoCorsoResponse(PagamentoCorsoBase):
    id: int
    ricevuta_id: int | None
    ricevuta: RicevutaInPagamentoCorso | None = None

    model_config = {"from_attributes": True}
