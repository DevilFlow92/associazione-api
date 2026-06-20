from __future__ import annotations

from pydantic import BaseModel


class TipoSpartitoInSpartito(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class StrumentoInSpartito(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


class DocumentoInSpartito(BaseModel):
    id: int
    nome: str

    model_config = {"from_attributes": True}


class SpartitoBase(BaseModel):
    banda_codice: int
    tipo_spartito_codice: int
    strumento_codice: int | None = None
    documento_id: int
    scaffale: str | None = None
    ripiano: str | None = None
    cartella: str | None = None


class SpartitoCreate(SpartitoBase):
    pass


class SpartitoUpdate(BaseModel):
    banda_codice: int | None = None
    tipo_spartito_codice: int | None = None
    strumento_codice: int | None = None
    documento_id: int | None = None
    scaffale: str | None = None
    ripiano: str | None = None
    cartella: str | None = None


class SpartitoResponse(SpartitoBase):
    id: int
    tipo_spartito: TipoSpartitoInSpartito | None = None
    strumento: StrumentoInSpartito | None = None
    documento: DocumentoInSpartito | None = None

    model_config = {"from_attributes": True}
