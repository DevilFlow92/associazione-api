from __future__ import annotations

from pydantic import BaseModel

from app.schemas._types import TzNaiveDatetime
from app.schemas.servizio import IndirizzoInServizio


class CorsoInLezione(BaseModel):
    id: int
    anno: int

    model_config = {"from_attributes": True}


class LezioneBase(BaseModel):
    corso_id: int
    data_lezione: TzNaiveDatetime
    indirizzo_id: int | None = None
    note: str | None = None


class LezioneCreate(LezioneBase):
    pass


class LezioneUpdate(BaseModel):
    corso_id: int | None = None
    data_lezione: TzNaiveDatetime | None = None
    indirizzo_id: int | None = None
    note: str | None = None


class LezioneResponse(LezioneBase):
    id: int
    corso: CorsoInLezione
    indirizzo: IndirizzoInServizio | None = None

    model_config = {"from_attributes": True}
