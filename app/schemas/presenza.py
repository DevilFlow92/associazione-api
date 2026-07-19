from __future__ import annotations

from pydantic import BaseModel

from app.models.presenza import StatoPresenza


class PresenzaBase(BaseModel):
    servizio_id: int
    note: str | None = None


class PresenzaCreate(PresenzaBase):
    persona_id: int


class PresenzaUpdate(BaseModel):
    stato: StatoPresenza | None = None
    note: str | None = None


class PersonaInPresenza(BaseModel):
    id: int
    nome: str | None = None
    cognome: str | None = None
    ragione_sociale: str | None = None

    model_config = {"from_attributes": True}


class PresenzaResponse(BaseModel):
    id: int
    persona_id: int
    servizio_id: int | None = None
    stato: StatoPresenza | None = None
    note: str | None = None
    persona: PersonaInPresenza | None = None

    model_config = {"from_attributes": True}
