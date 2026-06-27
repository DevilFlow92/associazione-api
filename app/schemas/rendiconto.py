from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class SottovoceRendicontoAggregato(BaseModel):
    codice: int
    descrizione: str
    totale: Decimal


class VoceRendicontoAggregato(BaseModel):
    codice: int
    descrizione: str
    totale: Decimal
    sottovoci: list[SottovoceRendicontoAggregato]


class SezioneRendicontoAggregato(BaseModel):
    codice: int
    descrizione: str
    totale: Decimal
    voci: list[VoceRendicontoAggregato]


class RendicontoTotali(BaseModel):
    entrate: Decimal
    uscite: Decimal
    avanzo_disavanzo: Decimal
    saldo_finale_cassa: Decimal
    saldo_finale_banca: Decimal


class RendicontoResponse(BaseModel):
    banda_codice: int
    banda_nome: str = ""
    anno: int
    chiuso: bool
    saldo_iniziale_cassa: Decimal
    saldo_iniziale_banca: Decimal
    sezioni: list[SezioneRendicontoAggregato]
    totali: RendicontoTotali


class RendicontoMensileItem(BaseModel):
    mese: int
    entrate: Decimal
    uscite: Decimal


class RendicontoMensileResponse(BaseModel):
    banda_codice: int
    anno: int
    mensile: list[RendicontoMensileItem]
