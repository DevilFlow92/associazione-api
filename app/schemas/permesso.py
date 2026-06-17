from __future__ import annotations

from pydantic import BaseModel


class PermessoResponse(BaseModel):
    codice: str
    descrizione: str

    model_config = {"from_attributes": True}
