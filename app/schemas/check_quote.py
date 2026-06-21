from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

StatoQuota = Literal["OK", "PARZIALE", "MANCANTE", "SOVRAPPIU", "NON_DOVUTA"]


class CheckQuotaSocio(BaseModel):
    socio_id: int
    codice_socio: str
    nome: str | None
    cognome: str | None
    quota_attesa: Decimal
    quota_versata: Decimal
    differenza: Decimal
    stato: StatoQuota


class CheckQuoteTotali(BaseModel):
    totale_atteso: Decimal
    totale_versato: Decimal
    totale_mancante: Decimal
    soci_ok: int
    soci_parziale: int
    soci_mancante: int
    soci_sovrappiu: int
    soci_non_dovuta: int


class CheckQuoteResponse(BaseModel):
    banda_codice: int
    anno: int
    quota_annuale_attesa: Decimal
    soci: list[CheckQuotaSocio]
    totali: CheckQuoteTotali
