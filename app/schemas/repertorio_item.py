from __future__ import annotations

from pydantic import BaseModel


class RepertorioItemBase(BaseModel):
    servizio_id: int
    ordine: int
    note: str | None = None


class RepertorioItemCreate(RepertorioItemBase):
    nome_parte_id: int


class RepertorioItemUpdate(BaseModel):
    ordine: int | None = None
    note: str | None = None


class NomeParteInRepertorioItem(BaseModel):
    id: int
    nome: str

    model_config = {"from_attributes": True}


class RepertorioItemResponse(BaseModel):
    id: int
    nome_parte_id: int
    servizio_id: int | None = None
    ordine: int
    note: str | None = None
    nome_parte: NomeParteInRepertorioItem | None = None

    model_config = {"from_attributes": True}
