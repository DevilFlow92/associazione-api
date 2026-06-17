from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.core.security import hash_password
from app.exceptions.auth import InvalidCredentialsError
from app.exceptions.persona import PersonaNotFoundError
from app.exceptions.utente import (
    RuoloNotFoundError,
    UtenteDuplicateEmailError,
    UtenteNotFoundError,
)
from app.repositories.persona_repository import PersonaRepository
from app.repositories.ruolo_repository import RuoloRepository
from app.repositories.utente_repository import UtenteRepository
from app.schemas.utente import UtenteCreate, UtenteResponse, UtenteUpdate


class UtenteService:
    def __init__(
        self,
        repo: UtenteRepository,
        ruolo_repo: RuoloRepository,
        persona_repo: PersonaRepository,
    ) -> None:
        self.repo = repo
        self.ruolo_repo = ruolo_repo
        self.persona_repo = persona_repo

    async def _resolve_ruoli(self, ruolo_ids: list[int]) -> list:
        ruoli = []
        for ruolo_id in ruolo_ids:
            ruolo = await self.ruolo_repo.get_by_id(ruolo_id)
            if not ruolo:
                raise RuoloNotFoundError(ruolo_id)
            ruoli.append(ruolo)
        return ruoli

    async def _check_persona(self, persona_id: int | None) -> None:
        if persona_id is not None:
            persona = await self.persona_repo.get_by_id(persona_id)
            if not persona:
                raise PersonaNotFoundError(persona_id)

    async def get_all(self, params: PageParams) -> PagedResponse[UtenteResponse]:
        utenti = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [UtenteResponse.model_validate(u) for u in utenti]
        return paginate(items, total, params)

    async def get_by_id(self, utente_id: int) -> UtenteResponse:
        utente = await self.repo.get_by_id(utente_id)
        if not utente:
            raise UtenteNotFoundError(utente_id)
        return UtenteResponse.model_validate(utente)

    async def create(self, data: UtenteCreate) -> UtenteResponse:
        if not data.password:
            # Sia gli umani sia i service account hanno bisogno di una credenziale
            # (login per gli umani, client-secret per i service account).
            raise InvalidCredentialsError()
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise UtenteDuplicateEmailError(data.email)
        await self._check_persona(data.persona_id)
        ruoli = await self._resolve_ruoli(data.ruoli)
        utente = await self.repo.create(
            tipo=data.tipo,
            email=data.email,
            password_hash=hash_password(data.password),
            nome_completo=data.nome_completo,
            persona_id=data.persona_id,
            superuser=data.superuser,
            ruoli=ruoli,
        )
        return UtenteResponse.model_validate(utente)

    async def update(self, utente_id: int, data: UtenteUpdate) -> UtenteResponse:
        utente = await self.repo.get_by_id(utente_id)
        if not utente:
            raise UtenteNotFoundError(utente_id)
        fields = data.model_dump(exclude_unset=True, exclude={"ruoli"})
        if "persona_id" in fields:
            await self._check_persona(fields["persona_id"])
        ruoli = (
            await self._resolve_ruoli(data.ruoli) if data.ruoli is not None else None
        )
        updated = await self.repo.update(utente, fields=fields, ruoli=ruoli)
        return UtenteResponse.model_validate(updated)

    async def set_password(self, utente_id: int, password: str) -> UtenteResponse:
        utente = await self.repo.get_by_id(utente_id)
        if not utente:
            raise UtenteNotFoundError(utente_id)
        updated = await self.repo.set_password(utente, hash_password(password))
        return UtenteResponse.model_validate(updated)

    async def delete(self, utente_id: int) -> None:
        utente = await self.repo.get_by_id(utente_id)
        if not utente:
            raise UtenteNotFoundError(utente_id)
        await self.repo.delete(utente)
