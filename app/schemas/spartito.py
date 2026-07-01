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


class NomeParteInSpartito(BaseModel):
    id: int
    nome: str

    model_config = {"from_attributes": True}


class DocumentoInNomeParte(BaseModel):
    id: int
    nome: str
    mime_type: str

    model_config = {"from_attributes": True}


# ── NomeParte schemas ─────────────────────────────────────────────────────────


class NomeParteCreate(BaseModel):
    nome: str
    tipo_spartito_codice: int
    banda_codice: int
    url_riferimento: str | None = None
    note: str | None = None
    documento_audio_id: int | None = None


class NomeParteUpdate(BaseModel):
    nome: str | None = None
    tipo_spartito_codice: int | None = None
    url_riferimento: str | None = None
    note: str | None = None
    documento_audio_id: int | None = None
    # banda_codice intentionally NOT updatable (ownership cannot change)


class NomeParteResponse(BaseModel):
    id: int
    nome: str
    tipo_spartito_codice: int
    banda_codice: int
    url_riferimento: str | None = None
    note: str | None = None
    documento_audio_id: int | None = None
    tipo_spartito: TipoSpartitoInSpartito | None = None
    documento_audio: DocumentoInNomeParte | None = None
    num_parti: int = 0  # filled by service layer, not from ORM directly

    model_config = {"from_attributes": True}


# ── Spartito schemas ──────────────────────────────────────────────────────────


class SpartitoBase(BaseModel):
    nome_parte_id: int
    banda_codice: int
    tipo_spartito_codice: int
    strumento_codice: int | None = None
    documento_id: int | None = None
    scaffale: str | None = None
    ripiano: str | None = None
    cartella: str | None = None


class SpartitoCreate(SpartitoBase):
    pass


class SpartitoUpdate(BaseModel):
    nome_parte_id: int | None = None
    banda_codice: int | None = None
    tipo_spartito_codice: int | None = None
    strumento_codice: int | None = None
    documento_id: int | None = None
    scaffale: str | None = None
    ripiano: str | None = None
    cartella: str | None = None


class SpartitoResponse(SpartitoBase):
    id: int
    nome_parte: NomeParteInSpartito | None = None
    tipo_spartito: TipoSpartitoInSpartito | None = None
    strumento: StrumentoInSpartito | None = None
    documento: DocumentoInSpartito | None = None

    model_config = {"from_attributes": True}
