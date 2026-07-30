from __future__ import annotations

from pydantic import BaseModel, model_validator

from app.models.presenza import StatoPresenza


class PresenzaBase(BaseModel):
    servizio_id: int | None = None
    prova_id: int | None = None
    lezione_id: int | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _arc_esclusivo(self) -> PresenzaBase:
        valorizzati = sum(
            x is not None for x in (self.servizio_id, self.prova_id, self.lezione_id)
        )
        if valorizzati != 1:
            raise ValueError(
                "Esattamente uno tra servizio_id, prova_id e lezione_id "
                "deve essere valorizzato"
            )
        return self


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
    prova_id: int | None = None
    lezione_id: int | None = None
    stato: StatoPresenza | None = None
    note: str | None = None
    persona: PersonaInPresenza | None = None

    model_config = {"from_attributes": True}


class PresenzaBulkUpdateItem(BaseModel):
    presenza_id: int
    stato: StatoPresenza | None = None
    note: str | None = None


class PresenzaBulkUpdate(BaseModel):
    items: list[PresenzaBulkUpdateItem]


class PresenzaBulkUpdateResponse(BaseModel):
    items: list[PresenzaResponse]
