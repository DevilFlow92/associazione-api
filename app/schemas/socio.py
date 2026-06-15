from __future__ import annotations

from pydantic import BaseModel


class SocioBase(BaseModel):
    codice_socio: str
    banda_codice: int
    ruolo_banda_codice: int


class SocioCreate(SocioBase):
    persona_id: int


class SocioUpdate(BaseModel):
    codice_socio: str | None = None
    banda_codice: int | None = None
    ruolo_banda_codice: int | None = None


class SocioResponse(SocioBase):
    id: int
    persona_id: int

    model_config = {"from_attributes": True}
