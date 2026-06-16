from __future__ import annotations

from pydantic import BaseModel


class LookupCreate(BaseModel):
    codice: int
    descrizione: str


class LookupUpdate(BaseModel):
    descrizione: str | None = None


class LookupResponse(BaseModel):
    codice: int
    descrizione: str

    model_config = {"from_attributes": True}


# ── Stato ────────────────────────────────────────────────────────────────────
class StatoCreate(LookupCreate):
    pass


class StatoUpdate(LookupUpdate):
    pass


class StatoResponse(LookupResponse):
    pass


# ── Regione ──────────────────────────────────────────────────────────────────
class RegioneCreate(LookupCreate):
    stato_codice: int | None = None


class RegioneUpdate(LookupUpdate):
    stato_codice: int | None = None


class RegioneResponse(LookupResponse):
    stato_codice: int | None = None


# ── Provincia ────────────────────────────────────────────────────────────────
class ProvinciaCreate(LookupCreate):
    sigla: str | None = None
    regione_codice: int | None = None


class ProvinciaUpdate(LookupUpdate):
    sigla: str | None = None
    regione_codice: int | None = None


class ProvinciaResponse(LookupResponse):
    sigla: str | None = None
    regione_codice: int | None = None


# ── Comune ───────────────────────────────────────────────────────────────────
class ComuneCreate(LookupCreate):
    codice_catastale: str | None = None
    provincia_codice: int | None = None


class ComuneUpdate(LookupUpdate):
    codice_catastale: str | None = None
    provincia_codice: int | None = None


class ComuneResponse(LookupResponse):
    codice_catastale: str | None = None
    provincia_codice: int | None = None


# ── Strumento ────────────────────────────────────────────────────────────────
class StrumentoCreate(LookupCreate):
    pass


class StrumentoUpdate(LookupUpdate):
    pass


class StrumentoResponse(LookupResponse):
    pass


# ── TipoIndirizzo ────────────────────────────────────────────────────────────
class TipoIndirizzoCreate(LookupCreate):
    pass


class TipoIndirizzoUpdate(LookupUpdate):
    pass


class TipoIndirizzoResponse(LookupResponse):
    pass


# ── Banda ────────────────────────────────────────────────────────────────────
class BandaCreate(LookupCreate):
    pass


class BandaUpdate(LookupUpdate):
    pass


class BandaResponse(LookupResponse):
    pass


# ── RuoloContatto ────────────────────────────────────────────────────────────
class RuoloContattoCreate(LookupCreate):
    pass


class RuoloContattoUpdate(LookupUpdate):
    pass


class RuoloContattoResponse(LookupResponse):
    pass


# ── RuoloBanda ───────────────────────────────────────────────────────────────
class RuoloBandaCreate(LookupCreate):
    pass


class RuoloBandaUpdate(LookupUpdate):
    pass


class RuoloBandaResponse(LookupResponse):
    pass


# ── SezioneRendiconto ────────────────────────────────────────────────────────
class SezioneRendicontoCreate(LookupCreate):
    pass


class SezioneRendicontoUpdate(LookupUpdate):
    pass


class SezioneRendicontoResponse(LookupResponse):
    pass


# ── VoceRendiconto ───────────────────────────────────────────────────────────
class VoceRendicontoCreate(LookupCreate):
    pass


class VoceRendicontoUpdate(LookupUpdate):
    pass


class VoceRendicontoResponse(LookupResponse):
    pass


# ── SottovoceRendiconto ──────────────────────────────────────────────────────
class SottovoceRendicontoCreate(LookupCreate):
    pass


class SottovoceRendicontoUpdate(LookupUpdate):
    pass


class SottovoceRendicontoResponse(LookupResponse):
    pass


# ── NaturaFlusso ─────────────────────────────────────────────────────────────
class NaturaFlussoCreate(LookupCreate):
    pass


class NaturaFlussoUpdate(LookupUpdate):
    pass


class NaturaFlussoResponse(LookupResponse):
    pass


# ── TipoDocumento ────────────────────────────────────────────────────────────
class TipoDocumentoCreate(LookupCreate):
    pass


class TipoDocumentoUpdate(LookupUpdate):
    pass


class TipoDocumentoResponse(LookupResponse):
    pass


# ── TipoSpartito ─────────────────────────────────────────────────────────────
class TipoSpartitoCreate(LookupCreate):
    pass


class TipoSpartitoUpdate(LookupUpdate):
    pass


class TipoSpartitoResponse(LookupResponse):
    pass


# ── StatoIscrizione ──────────────────────────────────────────────────────────
class StatoIscrizioneCreate(LookupCreate):
    pass


class StatoIscrizioneUpdate(LookupUpdate):
    pass


class StatoIscrizioneResponse(LookupResponse):
    pass
