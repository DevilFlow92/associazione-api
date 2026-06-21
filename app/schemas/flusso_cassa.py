from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.flusso_cassa import TipoFlussoCassa
from app.schemas._types import TzNaiveDatetime


class FlussoCassaBase(BaseModel):
    data_registrazione: TzNaiveDatetime
    descrizione_operazione: str
    note: str | None = None
    importo: float | None = None
    segno: str
    natura_flusso_codice: int
    tipo: TipoFlussoCassa = TipoFlussoCassa.MOVIMENTO
    iscrizione_id: int | None = None
    trasferimento_id: UUID | None = None


class FlussoCassaCreate(FlussoCassaBase):
    voce_contabilita_id: int


class FlussoCassaUpdate(BaseModel):
    data_registrazione: TzNaiveDatetime | None = None
    descrizione_operazione: str | None = None
    note: str | None = None
    importo: float | None = None
    segno: str | None = None
    natura_flusso_codice: int | None = None
    tipo: TipoFlussoCassa | None = None
    iscrizione_id: int | None = None
    trasferimento_id: UUID | None = None


class FlussoCassaResponse(FlussoCassaBase):
    id: int
    voce_contabilita_id: int

    model_config = {"from_attributes": True}


class TrasferimentoCreate(BaseModel):
    """Entry-point per il trasferimento atomico cassa↔banca.

    Genera due ``FlussoCassa`` correlati (uscita + entrata) condividendo lo
    stesso ``trasferimento_id``; vedi ``FlussoCassaService.crea_trasferimento``.
    """

    data_registrazione: TzNaiveDatetime
    importo: Decimal = Field(gt=0)
    natura_da_codice: int
    natura_a_codice: int
    voce_contabilita_id: int
    descrizione_operazione: str
    note: str | None = None


class TrasferimentoResponse(BaseModel):
    flussi: list[FlussoCassaResponse]
