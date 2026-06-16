from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DocumentoResponse(BaseModel):
    id: int
    nome: str
    tipo_documento_codice: int | None
    mime_type: str
    dimensione_bytes: int
    checksum: str
    caricato_il: datetime
    note: str | None
    file_path: str

    model_config = {"from_attributes": True}
