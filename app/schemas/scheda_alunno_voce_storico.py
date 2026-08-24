from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.scheda_alunno_voce import StatoVoceProgramma
from app.schemas.scheda_alunno import PersonaInSchedaAlunno


class SchedaAlunnoVoceStoricoResponse(BaseModel):
    """Sola lettura: nessun campo scrivibile, è consultazione dello storico
    append-only raccolto da #214 (mai esposto prima di questa card).
    """

    id: int
    stato_precedente: StatoVoceProgramma | None = None
    stato_nuovo: StatoVoceProgramma
    data_modifica: datetime
    modificato_da: PersonaInSchedaAlunno | None = None
    # Nullable perché la voce di catalogo di origine può essere stata
    # cancellata: ``voce_catalogo_id`` è denormalizzato di proposito (vedi
    # ``SchedaAlunnoVoceStorico``), quindi la riga resta consultabile anche
    # senza il testo.
    voce_testo: str | None = None

    model_config = {"from_attributes": True}
