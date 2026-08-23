from __future__ import annotations

from pydantic import BaseModel

from app.models.scheda_alunno_voce import StatoVoceProgramma
from app.schemas.voce_programma_catalogo import VoceProgrammaCatalogoResponse


class SchedaAlunnoVoceCreate(BaseModel):
    voce_catalogo_id: int
    stato: StatoVoceProgramma
    dettaglio: str | None = None
    ordine: int


class SchedaAlunnoVoceUpdate(BaseModel):
    stato: StatoVoceProgramma | None = None
    dettaglio: str | None = None
    ordine: int | None = None


class SchedaAlunnoVoceResponse(BaseModel):
    id: int
    scheda_alunno_id: int
    voce_catalogo_id: int
    stato: StatoVoceProgramma
    dettaglio: str | None = None
    ordine: int
    # Annidato così l'insegnante vede il testo della voce di catalogo, non
    # solo il suo id — stesso pattern di ``tipo_corso``/``categoria`` già
    # usati da ``VoceProgrammaCatalogoResponse``.
    voce_catalogo: VoceProgrammaCatalogoResponse

    model_config = {"from_attributes": True}
