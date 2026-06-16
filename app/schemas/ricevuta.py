from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RicevutaBase(BaseModel):
    data_ricevuta: datetime
    importo: float
    note_in_stampa: str | None = None
    note_fuori_stampa: str | None = None


class RicevutaCreate(RicevutaBase):
    servizio_id: int | None = None
    esterno_id: int | None = None
    documento_id: int | None = None


class RicevutaUpdate(BaseModel):
    data_ricevuta: datetime | None = None
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

    model_config = {"from_attributes": True}
