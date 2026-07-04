from __future__ import annotations

from pydantic import BaseModel

from app.mergefields.base import MergeFieldType


class MergeFieldSchema(BaseModel):
    chiave: str
    etichetta: str
    tipo: MergeFieldType


class MergeFieldsResponse(BaseModel):
    entita: dict[str, list[MergeFieldSchema]]
