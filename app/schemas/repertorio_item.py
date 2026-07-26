from __future__ import annotations

from pydantic import BaseModel, model_validator


class RepertorioItemBase(BaseModel):
    servizio_id: int | None = None
    prova_id: int | None = None
    ordine: int
    note: str | None = None

    @model_validator(mode="after")
    def _arc_esclusivo(self) -> RepertorioItemBase:
        if (self.servizio_id is None) == (self.prova_id is None):
            raise ValueError(
                "Esattamente uno tra servizio_id e prova_id deve essere valorizzato"
            )
        return self


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
    prova_id: int | None = None
    ordine: int
    note: str | None = None
    nome_parte: NomeParteInRepertorioItem | None = None

    model_config = {"from_attributes": True}
