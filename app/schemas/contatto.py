from __future__ import annotations

from pydantic import BaseModel


class ContattoBase(BaseModel):
    ruolo_contatto_codice: int
    email: str | None = None
    telefono: str | None = None


class ContattoCreate(ContattoBase):
    persona_id: int


class ContattoUpdate(BaseModel):
    ruolo_contatto_codice: int | None = None
    email: str | None = None
    telefono: str | None = None


class ContattoResponse(ContattoBase):
    id: int
    persona_id: int

    model_config = {"from_attributes": True}
