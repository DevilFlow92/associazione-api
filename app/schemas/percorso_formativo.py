from __future__ import annotations

from pydantic import BaseModel

from app.schemas.iscrizione_corso import CorsoInIscrizioneCorso


class RiepilogoVociPercorsoFormativo(BaseModel):
    totale: int
    da_iniziare: int
    in_corso: int
    acquisita: int


class TappaPercorsoFormativo(BaseModel):
    """Una iscrizione a corso della persona, con il riepilogo della sua
    scheda alunno se già creata dall'insegnante — vedi
    ``PercorsoFormativoService``."""

    iscrizione_corso_id: int
    corso: CorsoInIscrizioneCorso
    scheda_alunno_id: int | None = None
    riepilogo_voci: RiepilogoVociPercorsoFormativo
