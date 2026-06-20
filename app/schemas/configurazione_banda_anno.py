from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.voce_contabilita import VoceContabilitaResponse


class UtenteMinimal(BaseModel):
    id: int
    email: str

    model_config = {"from_attributes": True}


class ConfigurazioneBandaAnnoBase(BaseModel):
    banda_codice: int
    anno: int
    quota_annuale_attesa: Decimal = Decimal("0")
    saldo_iniziale_cassa: Decimal = Decimal("0")
    saldo_iniziale_banca: Decimal = Decimal("0")
    voce_contabilita_quote_id: int | None = None
    chiuso: bool = False
    data_chiusura: datetime | None = None
    chiuso_da_utente_id: int | None = None


class ConfigurazioneBandaAnnoCreate(ConfigurazioneBandaAnnoBase):
    pass


class ConfigurazioneBandaAnnoUpdate(BaseModel):
    quota_annuale_attesa: Decimal | None = None
    saldo_iniziale_cassa: Decimal | None = None
    saldo_iniziale_banca: Decimal | None = None
    voce_contabilita_quote_id: int | None = None
    chiuso: bool | None = None
    data_chiusura: datetime | None = None
    chiuso_da_utente_id: int | None = None


class ConfigurazioneBandaAnnoResponse(ConfigurazioneBandaAnnoBase):
    id: int
    voce_contabilita_quote: VoceContabilitaResponse | None = None
    chiuso_da_utente: UtenteMinimal | None = None

    model_config = {"from_attributes": True}
