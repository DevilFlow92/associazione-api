from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, computed_field

from app.models.utente import TipoUtente
from app.schemas.ruolo import RuoloResponse


class UtenteBase(BaseModel):
    email: EmailStr
    nome_completo: str | None = None
    persona_id: int | None = None


class UtenteCreate(UtenteBase):
    tipo: TipoUtente = TipoUtente.UMANO
    # Obbligatoria per gli utenti umani; ignorata per i service account
    # (validata nel service).
    password: str | None = None
    superuser: bool = False
    ruoli: list[int] = []


class UtenteUpdate(BaseModel):
    nome_completo: str | None = None
    attivo: bool | None = None
    superuser: bool | None = None
    persona_id: int | None = None
    # Se fornito, sostituisce l'intero set di ruoli dell'utente.
    ruoli: list[int] | None = None


class PasswordUpdate(BaseModel):
    password: str


class UtenteResponse(UtenteBase):
    id: int
    tipo: TipoUtente
    attivo: bool
    superuser: bool
    creato_il: datetime
    ruoli: list[RuoloResponse]

    @computed_field
    @property
    def permessi(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for ruolo in self.ruoli:
            for p in ruolo.permessi:
                if p.codice not in seen:
                    seen.add(p.codice)
                    result.append(p.codice)
        return result

    model_config = {"from_attributes": True}
