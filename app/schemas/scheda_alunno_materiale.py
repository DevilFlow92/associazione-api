from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, computed_field


class SchedaAlunnoMaterialeLinkCreate(BaseModel):
    titolo: str
    url: str


class SchedaAlunnoMaterialeResponse(BaseModel):
    id: int
    scheda_alunno_id: int
    titolo: str
    storage_key: str | None = None
    nome_file_originale: str | None = None
    mime_type: str | None = None
    dimensione_bytes: int | None = None
    url: str | None = None
    caricato_da_persona_id: int | None = None
    data_caricamento: datetime

    model_config = {"from_attributes": True}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tipo(self) -> Literal["file", "link"]:
        return "file" if self.storage_key is not None else "link"
