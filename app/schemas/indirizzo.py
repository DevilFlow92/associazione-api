from __future__ import annotations

from pydantic import BaseModel


class IndirizzoBase(BaseModel):
    tipo_indirizzo_codice: int
    prima_riga: str | None = None
    seconda_riga: str | None = None
    comune_codice: int | None = None
    cap: str | None = None
    numero_civico: str | None = None
    interno: str | None = None


class IndirizzoCreate(IndirizzoBase):
    pass


class IndirizzoUpdate(BaseModel):
    tipo_indirizzo_codice: int | None = None
    prima_riga: str | None = None
    seconda_riga: str | None = None
    comune_codice: int | None = None
    cap: str | None = None
    numero_civico: str | None = None
    interno: str | None = None


class IndirizzoResponse(IndirizzoBase):
    id: int

    model_config = {"from_attributes": True}
