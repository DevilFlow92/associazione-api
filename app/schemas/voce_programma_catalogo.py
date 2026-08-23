from __future__ import annotations

from pydantic import BaseModel


class TipoCorsoInVoceProgramma(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class CategoriaInVoceProgramma(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class VoceProgrammaCatalogoCreate(BaseModel):
    tipo_corso_codice: int
    categoria_codice: int
    testo: str
    livello: int = 1
    attiva: bool = True


class VoceProgrammaCatalogoUpdate(BaseModel):
    """``tipo_corso_codice`` non è modificabile: se si sbaglia tipo corso si
    disattiva la voce (``attiva=False``) e se ne crea una nuova."""

    categoria_codice: int | None = None
    testo: str | None = None
    livello: int | None = None
    attiva: bool | None = None


class VoceProgrammaCatalogoResponse(BaseModel):
    id: int
    tipo_corso_codice: int
    categoria_codice: int
    testo: str
    livello: int
    attiva: bool
    tipo_corso: TipoCorsoInVoceProgramma
    categoria: CategoriaInVoceProgramma

    model_config = {"from_attributes": True}
