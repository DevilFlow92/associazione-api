from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.codice_progressivo import CodiceProgressivoError
from app.exceptions.esterno import EsternoDuplicateCodiceError, EsternoNotFoundError
from app.exceptions.persona import PersonaNotFoundError
from app.repositories.esterno_repository import EsternoRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.esterno import EsternoCreate, EsternoResponse, EsternoUpdate
from app.services.codice_progressivo import (
    LOCK_KEY_ESTERNO,
    MAX_TENTATIVI,
    lock_banda,
    next_codice_progressivo,
)


class EsternoService:
    def __init__(
        self, repo: EsternoRepository, persona_repo: PersonaRepository
    ) -> None:
        self.repo = repo
        self.persona_repo = persona_repo

    async def get_all(
        self, params: PageParams, banda_codice: int | None = None
    ) -> PagedResponse[EsternoResponse]:
        esterni = await self.repo.get_all(
            offset=params.offset, limit=params.limit, banda_codice=banda_codice
        )
        total = await self.repo.count_all(banda_codice=banda_codice)
        items = [EsternoResponse.model_validate(e) for e in esterni]
        return paginate(items, total, params)

    async def get_by_id(self, esterno_id: int) -> EsternoResponse:
        esterno = await self.repo.get_by_id(esterno_id)
        if not esterno:
            raise EsternoNotFoundError(esterno_id)
        return EsternoResponse.model_validate(esterno)

    async def create(self, data: EsternoCreate) -> EsternoResponse:
        persona = await self.persona_repo.get_by_id(data.persona_id)
        if not persona:
            raise PersonaNotFoundError(data.persona_id)
        codice_esterno = await self._genera_codice_esterno(persona.banda_codice)
        esterno = await self.repo.create(data, codice_esterno)
        return EsternoResponse.model_validate(esterno)

    async def _genera_codice_esterno(self, banda_codice: int) -> str:
        await lock_banda(self.repo.db, LOCK_KEY_ESTERNO, banda_codice)
        for _ in range(MAX_TENTATIVI):
            esistenti = await self.repo.get_codici_by_banda(banda_codice)
            candidato = next_codice_progressivo(esistenti)
            if not await self.repo.get_by_codice(candidato, banda_codice):
                return candidato
        raise CodiceProgressivoError("esterno", banda_codice, MAX_TENTATIVI)

    async def update(self, esterno_id: int, data: EsternoUpdate) -> EsternoResponse:
        esterno = await self.repo.get_by_id(esterno_id)
        if not esterno:
            raise EsternoNotFoundError(esterno_id)
        banda = esterno.persona.banda_codice
        if data.codice_esterno and data.codice_esterno != esterno.codice_esterno:
            await lock_banda(self.repo.db, LOCK_KEY_ESTERNO, banda)
            existing = await self.repo.get_by_codice(data.codice_esterno, banda)
            if existing and existing.id != esterno_id:
                raise EsternoDuplicateCodiceError(data.codice_esterno)
        updated = await self.repo.update(esterno, data)
        return EsternoResponse.model_validate(updated)

    async def delete(self, esterno_id: int) -> None:
        esterno = await self.repo.get_by_id(esterno_id)
        if not esterno:
            raise EsternoNotFoundError(esterno_id)
        await self.repo.delete(esterno)
