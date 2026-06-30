from __future__ import annotations

from pydantic import BaseModel


class MacroSezioneResponse(BaseModel):
    codice: int
    nome: str
    permesso_prefisso: str
    ordine: int

    model_config = {"from_attributes": True}
