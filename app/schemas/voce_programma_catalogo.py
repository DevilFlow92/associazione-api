from __future__ import annotations

from pydantic import BaseModel


class TipoCorsoInVoceProgramma(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class VoceProgrammaCatalogoCreate(BaseModel):
    tipo_corso_codice: int
    categoria: str
    testo: str
    attiva: bool = True


class VoceProgrammaCatalogoUpdate(BaseModel):
    """``tipo_corso_codice`` non è modificabile: se si sbaglia tipo corso si
    disattiva la voce (``attiva=False``) e se ne crea una nuova."""

    categoria: str | None = None
    testo: str | None = None
    attiva: bool | None = None


class VoceProgrammaCatalogoResponse(BaseModel):
    id: int
    tipo_corso_codice: int
    categoria: str
    testo: str
    attiva: bool
    tipo_corso: TipoCorsoInVoceProgramma

    model_config = {"from_attributes": True}
