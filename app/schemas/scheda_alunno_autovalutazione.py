from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SchedaAlunnoAutovalutazioneCreate(BaseModel):
    testo: str


class SchedaAlunnoAutovalutazioneUpdate(BaseModel):
    testo: str


class SchedaAlunnoAutovalutazioneResponse(BaseModel):
    id: int
    scheda_alunno_id: int
    # Audit: sempre l'alunno titolare della scheda, derivato dall'utente
    # autenticato al momento della scrittura, mai accettato dal payload —
    # vedi ``SchedaAlunnoAutovalutazioneService``.
    persona_id: int
    testo: str
    data_creazione: datetime
    data_modifica: datetime | None = None

    model_config = {"from_attributes": True}
