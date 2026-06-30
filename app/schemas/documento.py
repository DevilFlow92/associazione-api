from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TipoDocumentoInDocumento(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class SottoCartellaInDocumento(BaseModel):
    id: int
    nome: str

    model_config = {"from_attributes": True}


class DocumentoResponse(BaseModel):
    id: int
    nome: str
    tipo_documento_codice: int | None
    tipo_documento: TipoDocumentoInDocumento | None = None
    sotto_cartella_id: int | None
    sotto_cartella: SottoCartellaInDocumento | None = None
    mime_type: str
    dimensione_bytes: int
    checksum: str
    caricato_il: datetime
    note: str | None
    file_path: str

    model_config = {"from_attributes": True}
