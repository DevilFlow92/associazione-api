from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RicevutaBase(BaseModel):
    data_ricevuta: datetime
    importo: float
    note_in_stampa: str | None = None
    note_fuori_stampa: str | None = None


class RicevutaCreate(RicevutaBase):
    servizio_id: int
    esterno_id: int


class RicevutaUpdate(BaseModel):
    data_ricevuta: datetime | None = None
    importo: float | None = None
    note_in_stampa: str | None = None
    note_fuori_stampa: str | None = None


class RicevutaResponse(RicevutaBase):
    id: int
    servizio_id: int
    esterno_id: int

    model_config = {"from_attributes": True}
