from __future__ import annotations

from pydantic import BaseModel

from app.schemas._types import TzNaiveDatetime


class FlussoCassaBase(BaseModel):
    data_registrazione: TzNaiveDatetime
    descrizione_operazione: str
    note: str | None = None
    importo: float | None = None
    segno: str
    natura_flusso_codice: int


class FlussoCassaCreate(FlussoCassaBase):
    voce_contabilita_id: int


class FlussoCassaUpdate(BaseModel):
    data_registrazione: TzNaiveDatetime | None = None
    descrizione_operazione: str | None = None
    note: str | None = None
    importo: float | None = None
    segno: str | None = None
    natura_flusso_codice: int | None = None


class FlussoCassaResponse(FlussoCassaBase):
    id: int
    voce_contabilita_id: int

    model_config = {"from_attributes": True}
