from __future__ import annotations

from pydantic import BaseModel

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

    model_config = {"from_attributes": True}
