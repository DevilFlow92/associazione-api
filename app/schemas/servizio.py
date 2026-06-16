from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ServizioBase(BaseModel):
    banda_codice: int
    anno: int
    descrizione_servizio: str
    data_servizio: datetime
    indirizzo_id: int
    note: str | None = None


class ServizioCreate(ServizioBase):
    pass


class ServizioUpdate(BaseModel):
    banda_codice: int | None = None
    anno: int | None = None
    descrizione_servizio: str | None = None
    data_servizio: datetime | None = None
    indirizzo_id: int | None = None
    note: str | None = None


class ServizioResponse(ServizioBase):
    id: int

    model_config = {"from_attributes": True}
