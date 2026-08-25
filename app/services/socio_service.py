from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.codice_progressivo import CodiceProgressivoError
from app.exceptions.persona import PersonaNotFoundError
from app.exceptions.socio import SocioDuplicateCodiceError, SocioNotFoundError
from app.repositories.persona_repository import PersonaRepository
from app.repositories.socio_repository import SocioRepository
from app.schemas.socio import SocioCreate, SocioResponse, SocioUpdate
from app.services.codice_progressivo import (
    LOCK_KEY_SOCIO,
    MAX_TENTATIVI,
    lock_banda,
    next_codice_progressivo,
)


class SocioService:
    def __init__(self, repo: SocioRepository, persona_repo: PersonaRepository) -> None:
        self.repo = repo
        self.persona_repo = persona_repo

    async def get_all(
        self, params: PageParams, banda_codice: int | None = None
    ) -> PagedResponse[SocioResponse]:
        soci = await self.repo.get_all(
            offset=params.offset, limit=params.limit, banda_codice=banda_codice
        )
        total = await self.repo.count_all(banda_codice=banda_codice)
        items = [SocioResponse.model_validate(s) for s in soci]
        return paginate(items, total, params)

    async def get_by_id(self, socio_id: int) -> SocioResponse:
        socio = await self.repo.get_by_id(socio_id)
        if not socio:
            raise SocioNotFoundError(socio_id)
        return SocioResponse.model_validate(socio)

    async def create(self, data: SocioCreate) -> SocioResponse:
        persona = await self.persona_repo.get_by_id(data.persona_id)
        if not persona:
            raise PersonaNotFoundError(data.persona_id)
        codice_socio = await self._genera_codice_socio(persona.banda_codice)
        socio = await self.repo.create(data, codice_socio)
        return SocioResponse.model_validate(socio)

    async def _genera_codice_socio(self, banda_codice: int) -> str:
        await lock_banda(self.repo.db, LOCK_KEY_SOCIO, banda_codice)
        for _ in range(MAX_TENTATIVI):
            esistenti = await self.repo.get_codici_by_banda(banda_codice)
            candidato = next_codice_progressivo(esistenti)
            if not await self.repo.get_by_codice(candidato, banda_codice):
                return candidato
        raise CodiceProgressivoError("socio", banda_codice, MAX_TENTATIVI)

    async def update(self, socio_id: int, data: SocioUpdate) -> SocioResponse:
        socio = await self.repo.get_by_id(socio_id)
        if not socio:
            raise SocioNotFoundError(socio_id)
        banda = socio.persona.banda_codice
        if data.codice_socio and data.codice_socio != socio.codice_socio:
            await lock_banda(self.repo.db, LOCK_KEY_SOCIO, banda)
            existing = await self.repo.get_by_codice(data.codice_socio, banda)
            if existing and existing.id != socio_id:
                raise SocioDuplicateCodiceError(data.codice_socio, banda)
        updated = await self.repo.update(socio, data)
        return SocioResponse.model_validate(updated)

    async def delete(self, socio_id: int) -> None:
        socio = await self.repo.get_by_id(socio_id)
        if not socio:
            raise SocioNotFoundError(socio_id)
        await self.repo.delete(socio)
