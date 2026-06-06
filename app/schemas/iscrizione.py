from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.models.iscrizione import StatoPagamento


class IscrizioneBase(BaseModel):
    anno: int
    quota_dovuta: float
    quota_pagata: float = 0
    stato_pagamento: StatoPagamento = StatoPagamento.NON_PAGATO
    note: str | None = None


class IscrizioneCreate(IscrizioneBase):
    socio_id: int


class IscrizioneUpdate(BaseModel):
    quota_pagata: float | None = None
    stato_pagamento: StatoPagamento | None = None
    note: str | None = None


class IscrizioneResponse(IscrizioneBase):
    id: int
    socio_id: int
    data_iscrizione: date

    model_config = {"from_attributes": True}
