from __future__ import annotations

from pydantic import BaseModel

from app.schemas.scheda_alunno_autovalutazione import (
    SchedaAlunnoAutovalutazioneResponse,
)
from app.schemas.scheda_alunno_materiale import SchedaAlunnoMaterialeResponse
from app.schemas.scheda_alunno_voce import SchedaAlunnoVoceResponse


class PersonaInSchedaAlunno(BaseModel):
    id: int
    nome: str | None = None
    cognome: str | None = None

    model_config = {"from_attributes": True}


class IscrizioneCorsoInSchedaAlunno(BaseModel):
    id: int
    corso_id: int
    persona_id: int

    model_config = {"from_attributes": True}


class SchedaAlunnoBase(BaseModel):
    note: str | None = None


class SchedaAlunnoCreate(SchedaAlunnoBase):
    iscrizione_corso_id: int


class SchedaAlunnoUpdate(BaseModel):
    note: str | None = None


class SchedaAlunnoResponse(SchedaAlunnoBase):
    id: int
    iscrizione_corso_id: int
    # Audit: derivato dall'utente autenticato al momento della scrittura,
    # mai accettato dal payload — vedi ``SchedaAlunnoService``.
    aggiornato_da_persona_id: int | None = None
    iscrizione_corso: IscrizioneCorsoInSchedaAlunno
    aggiornato_da: PersonaInSchedaAlunno | None = None
    # Ordinata per ``ordine`` grazie a ``SchedaAlunno.voci`` (relationship
    # con order_by), non qui: nessun sort applicato lato schema.
    voci: list[SchedaAlunnoVoceResponse] = []
    # Annidati per coerenza con ``voci`` (vedi card #217). A differenza delle
    # voci non contengono il contenuto del file, solo i metadati — il peso
    # resta contenuto anche con molti materiali allegati.
    materiali: list[SchedaAlunnoMaterialeResponse] = []
    # Ordinate per data di creazione decrescente grazie a
    # ``SchedaAlunno.autovalutazioni`` (relationship con order_by), non qui:
    # nessun sort applicato lato schema. Scritte dall'alunno stesso (card
    # #218), non dal personale corsi — vedi ``rbac_row_level``.
    autovalutazioni: list[SchedaAlunnoAutovalutazioneResponse] = []

    model_config = {"from_attributes": True}
