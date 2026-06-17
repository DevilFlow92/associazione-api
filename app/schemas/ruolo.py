from __future__ import annotations

from pydantic import BaseModel

from app.schemas.permesso import PermessoResponse


class RuoloBase(BaseModel):
    nome: str
    descrizione: str | None = None
    banda_codice: int | None = None


class RuoloCreate(RuoloBase):
    # Codici permesso da assegnare al ruolo alla creazione (opzionale).
    permessi: list[str] = []


class RuoloUpdate(BaseModel):
    nome: str | None = None
    descrizione: str | None = None
    banda_codice: int | None = None
    # Se fornito, sostituisce l'intero set di permessi del ruolo.
    permessi: list[str] | None = None


class RuoloResponse(RuoloBase):
    id: int
    permessi: list[PermessoResponse]

    model_config = {"from_attributes": True}
