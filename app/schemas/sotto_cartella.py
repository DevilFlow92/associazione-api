from __future__ import annotations

from pydantic import BaseModel


class SottoCartellaBase(BaseModel):
    nome: str
    macro_sezione_codice: int


class SottoCartellaCreate(SottoCartellaBase):
    pass


class SottoCartellaUpdate(BaseModel):
    nome: str | None = None


class SottoCartellaResponse(SottoCartellaBase):
    id: int

    model_config = {"from_attributes": True}
