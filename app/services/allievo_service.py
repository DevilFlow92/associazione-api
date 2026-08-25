from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.allievo import (
    AllievoDuplicateCodiceError,
    AllievoNotFoundError,
    AllievoPersonaAlreadyLinkedError,
)
from app.exceptions.codice_progressivo import CodiceProgressivoError
from app.exceptions.persona import PersonaNotFoundError
from app.repositories.allievo_repository import AllievoRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.allievo import AllievoCreate, AllievoResponse, AllievoUpdate
from app.services.codice_progressivo import (
    LOCK_KEY_ALLIEVO,
    MAX_TENTATIVI,
    lock_banda,
    next_codice_progressivo,
)


class AllievoService:
    def __init__(
        self, repo: AllievoRepository, persona_repo: PersonaRepository
    ) -> None:
        self.repo = repo
        self.persona_repo = persona_repo

    async def get_all(
        self, params: PageParams, banda_codice: int | None = None
    ) -> PagedResponse[AllievoResponse]:
        allievi = await self.repo.get_all(
            offset=params.offset, limit=params.limit, banda_codice=banda_codice
        )
        total = await self.repo.count_all(banda_codice=banda_codice)
        items = [AllievoResponse.model_validate(a) for a in allievi]
        return paginate(items, total, params)

    async def get_by_id(self, allievo_id: int) -> AllievoResponse:
        allievo = await self.repo.get_by_id(allievo_id)
        if not allievo:
            raise AllievoNotFoundError(allievo_id)
        return AllievoResponse.model_validate(allievo)

    async def create(self, data: AllievoCreate) -> AllievoResponse:
        persona = await self.persona_repo.get_by_id(data.persona_id)
        if not persona:
            raise PersonaNotFoundError(data.persona_id)
        existing_persona_link = await self.repo.get_by_persona_id(data.persona_id)
        if existing_persona_link:
            raise AllievoPersonaAlreadyLinkedError(data.persona_id)
        codice_allievo = await self._genera_codice_allievo(persona.banda_codice)
        allievo = await self.repo.create(data, codice_allievo)
        return AllievoResponse.model_validate(allievo)

    async def _genera_codice_allievo(self, banda_codice: int) -> str:
        await lock_banda(self.repo.db, LOCK_KEY_ALLIEVO, banda_codice)
        for _ in range(MAX_TENTATIVI):
            esistenti = await self.repo.get_codici_by_banda(banda_codice)
            candidato = next_codice_progressivo(esistenti)
            if not await self.repo.get_by_codice(candidato, banda_codice):
                return candidato
        raise CodiceProgressivoError("allievo", banda_codice, MAX_TENTATIVI)

    async def update(self, allievo_id: int, data: AllievoUpdate) -> AllievoResponse:
        allievo = await self.repo.get_by_id(allievo_id)
        if not allievo:
            raise AllievoNotFoundError(allievo_id)
        banda = allievo.persona.banda_codice
        if data.codice_allievo and data.codice_allievo != allievo.codice_allievo:
            await lock_banda(self.repo.db, LOCK_KEY_ALLIEVO, banda)
            existing = await self.repo.get_by_codice(data.codice_allievo, banda)
            if existing and existing.id != allievo_id:
                raise AllievoDuplicateCodiceError(data.codice_allievo)
        updated = await self.repo.update(allievo, data)
        return AllievoResponse.model_validate(updated)

    async def delete(self, allievo_id: int) -> None:
        allievo = await self.repo.get_by_id(allievo_id)
        if not allievo:
            raise AllievoNotFoundError(allievo_id)
        await self.repo.delete(allievo)
