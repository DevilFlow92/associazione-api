from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.documento import TipoDocumento


class DocumentoResponse(BaseModel):
    id: int
    nome: str
    tipo: TipoDocumento
    mime_type: str
    dimensione_bytes: int
    checksum: str
    socio_id: int | None
    caricato_il: datetime
    note: str | None

    model_config = {"from_attributes": True}
