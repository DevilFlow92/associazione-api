from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class IscrizioneBase(BaseModel):
    socio_id: int
    anno: int
    quota_partecipazione: float
    stato_iscrizione_codice: int
    data_iscrizione: date
    documento_id: int | None = None
    ricevuta_id: int | None = None
    note: str | None = None


class IscrizioneCreate(IscrizioneBase):
    pass


class IscrizioneUpdate(BaseModel):
    anno: int | None = None
    quota_partecipazione: float | None = None
    stato_iscrizione_codice: int | None = None
    data_iscrizione: date | None = None
    documento_id: int | None = None
    ricevuta_id: int | None = None
    note: str | None = None


class IscrizioneResponse(IscrizioneBase):
    id: int

    model_config = {"from_attributes": True}
