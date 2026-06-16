from __future__ import annotations

from pydantic import BaseModel


class SpartitoBase(BaseModel):
    tipo_spartito_codice: int
    strumento_codice: int | None = None
    documento_id: int
    scaffale: str | None = None
    ripiano: str | None = None
    cartella: str | None = None


class SpartitoCreate(SpartitoBase):
    pass


class SpartitoUpdate(BaseModel):
    tipo_spartito_codice: int | None = None
    strumento_codice: int | None = None
    documento_id: int | None = None
    scaffale: str | None = None
    ripiano: str | None = None
    cartella: str | None = None


class SpartitoResponse(SpartitoBase):
    id: int

    model_config = {"from_attributes": True}
