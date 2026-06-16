from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.flusso_cassa import FlussoCassaNotFoundError
from app.exceptions.voce_contabilita import VoceContabilitaNotFoundError
from app.repositories.flusso_cassa_repository import FlussoCassaRepository
from app.repositories.voce_contabilita_repository import VoceContabilitaRepository
from app.schemas.flusso_cassa import (
    FlussoCassaCreate,
    FlussoCassaResponse,
    FlussoCassaUpdate,
)


class FlussoCassaService:
    def __init__(
        self, repo: FlussoCassaRepository, voce_repo: VoceContabilitaRepository
    ) -> None:
        self.repo = repo
        self.voce_repo = voce_repo

    async def get_all(self, params: PageParams) -> PagedResponse[FlussoCassaResponse]:
        flussi = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [FlussoCassaResponse.model_validate(f) for f in flussi]
        return paginate(items, total, params)

    async def get_by_voce(
        self, voce_contabilita_id: int, params: PageParams
    ) -> PagedResponse[FlussoCassaResponse]:
        voce = await self.voce_repo.get_by_id(voce_contabilita_id)
        if not voce:
            raise VoceContabilitaNotFoundError(voce_contabilita_id)
        flussi = await self.repo.get_by_voce(
            voce_contabilita_id, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_by_voce(voce_contabilita_id)
        items = [FlussoCassaResponse.model_validate(f) for f in flussi]
        return paginate(items, total, params)

    async def get_by_id(self, flusso_id: int) -> FlussoCassaResponse:
        flusso = await self.repo.get_by_id(flusso_id)
        if not flusso:
            raise FlussoCassaNotFoundError(flusso_id)
        return FlussoCassaResponse.model_validate(flusso)

    async def create(self, data: FlussoCassaCreate) -> FlussoCassaResponse:
        voce = await self.voce_repo.get_by_id(data.voce_contabilita_id)
        if not voce:
            raise VoceContabilitaNotFoundError(data.voce_contabilita_id)
        flusso = await self.repo.create(data)
        return FlussoCassaResponse.model_validate(flusso)

    async def update(
        self, flusso_id: int, data: FlussoCassaUpdate
    ) -> FlussoCassaResponse:
        flusso = await self.repo.get_by_id(flusso_id)
        if not flusso:
            raise FlussoCassaNotFoundError(flusso_id)
        updated = await self.repo.update(flusso, data)
        return FlussoCassaResponse.model_validate(updated)

    async def delete(self, flusso_id: int) -> None:
        flusso = await self.repo.get_by_id(flusso_id)
        if not flusso:
            raise FlussoCassaNotFoundError(flusso_id)
        await self.repo.delete(flusso)
