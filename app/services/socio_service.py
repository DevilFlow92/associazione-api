from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.persona import PersonaNotFoundError
from app.exceptions.socio import SocioDuplicateCodiceError, SocioNotFoundError
from app.repositories.persona_repository import PersonaRepository
from app.repositories.socio_repository import SocioRepository
from app.schemas.socio import SocioCreate, SocioResponse, SocioUpdate


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
        existing = await self.repo.get_by_codice(data.codice_socio, data.banda_codice)
        if existing:
            raise SocioDuplicateCodiceError(data.codice_socio, data.banda_codice)
        socio = await self.repo.create(data)
        return SocioResponse.model_validate(socio)

    async def update(self, socio_id: int, data: SocioUpdate) -> SocioResponse:
        socio = await self.repo.get_by_id(socio_id)
        if not socio:
            raise SocioNotFoundError(socio_id)
        codice = data.codice_socio or socio.codice_socio
        banda = data.banda_codice or socio.banda_codice
        existing = await self.repo.get_by_codice(codice, banda)
        if existing and existing.id != socio_id:
            raise SocioDuplicateCodiceError(codice, banda)
        updated = await self.repo.update(socio, data)
        return SocioResponse.model_validate(updated)

    async def delete(self, socio_id: int) -> None:
        socio = await self.repo.get_by_id(socio_id)
        if not socio:
            raise SocioNotFoundError(socio_id)
        await self.repo.delete(socio)
