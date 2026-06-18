from __future__ import annotations

from pydantic import BaseModel


class StrumentoInEsterno(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class EsternoBase(BaseModel):
    codice_esterno: str
    strumento_codice: int


class EsternoCreate(EsternoBase):
    persona_id: int


class EsternoUpdate(BaseModel):
    codice_esterno: str | None = None
    strumento_codice: int | None = None


class EsternoResponse(EsternoBase):
    id: int
    persona_id: int
    strumento: StrumentoInEsterno | None = None

    model_config = {"from_attributes": True}
