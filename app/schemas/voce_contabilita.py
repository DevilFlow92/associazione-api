from __future__ import annotations

from pydantic import BaseModel


class VoceContabilitaBase(BaseModel):
    banda_codice: int
    voce_contabilita: str
    sezione_rendiconto_codice: int
    voce_rendiconto_codice: int
    sottovoce_rendiconto_codice: int


class VoceContabilitaCreate(VoceContabilitaBase):
    pass


class VoceContabilitaUpdate(BaseModel):
    banda_codice: int | None = None
    voce_contabilita: str | None = None
    sezione_rendiconto_codice: int | None = None
    voce_rendiconto_codice: int | None = None
    sottovoce_rendiconto_codice: int | None = None


class VoceContabilitaResponse(VoceContabilitaBase):
    id: int

    model_config = {"from_attributes": True}
