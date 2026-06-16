from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.voce_contabilita import (
    VoceContabilitaHasFlussiError,
    VoceContabilitaNotFoundError,
)
from app.repositories.voce_contabilita_repository import VoceContabilitaRepository
from app.schemas.voce_contabilita import (
    VoceContabilitaCreate,
    VoceContabilitaResponse,
    VoceContabilitaUpdate,
)


class VoceContabilitaService:
    def __init__(self, repo: VoceContabilitaRepository) -> None:
        self.repo = repo

    async def get_all(
        self, banda_codice: int | None, params: PageParams
    ) -> PagedResponse[VoceContabilitaResponse]:
        voci = await self.repo.get_all(
            banda_codice=banda_codice, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_all(banda_codice=banda_codice)
        items = [VoceContabilitaResponse.model_validate(v) for v in voci]
        return paginate(items, total, params)

    async def get_by_id(self, voce_id: int) -> VoceContabilitaResponse:
        voce = await self.repo.get_by_id(voce_id)
        if not voce:
            raise VoceContabilitaNotFoundError(voce_id)
        return VoceContabilitaResponse.model_validate(voce)

    async def create(self, data: VoceContabilitaCreate) -> VoceContabilitaResponse:
        voce = await self.repo.create(data)
        return VoceContabilitaResponse.model_validate(voce)

    async def update(
        self, voce_id: int, data: VoceContabilitaUpdate
    ) -> VoceContabilitaResponse:
        voce = await self.repo.get_by_id(voce_id)
        if not voce:
            raise VoceContabilitaNotFoundError(voce_id)
        updated = await self.repo.update(voce, data)
        return VoceContabilitaResponse.model_validate(updated)

    async def delete(self, voce_id: int) -> None:
        voce = await self.repo.get_by_id(voce_id)
        if not voce:
            raise VoceContabilitaNotFoundError(voce_id)
        if await self.repo.has_flussi(voce_id):
            raise VoceContabilitaHasFlussiError(voce_id)
        await self.repo.delete(voce)
