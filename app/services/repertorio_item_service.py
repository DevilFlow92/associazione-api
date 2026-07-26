from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.prova import ProvaNotFoundError
from app.exceptions.repertorio_item import RepertorioItemNotFoundError
from app.exceptions.servizio import ServizioNotFoundError
from app.exceptions.spartito import NomeParteNotFoundError
from app.repositories.nome_parte_repository import NomeParteRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.repertorio_item_repository import RepertorioItemRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.repertorio_item import (
    RepertorioItemCreate,
    RepertorioItemResponse,
    RepertorioItemUpdate,
)


class RepertorioItemService:
    def __init__(
        self,
        repo: RepertorioItemRepository,
        nome_parte_repo: NomeParteRepository,
        servizio_repo: ServizioRepository,
        prova_repo: ProvaRepository,
    ) -> None:
        self.repo = repo
        self.nome_parte_repo = nome_parte_repo
        self.servizio_repo = servizio_repo
        self.prova_repo = prova_repo

    async def get_by_servizio(
        self, servizio_id: int, params: PageParams
    ) -> PagedResponse[RepertorioItemResponse]:
        servizio = await self.servizio_repo.get_by_id(servizio_id)
        if not servizio:
            raise ServizioNotFoundError(servizio_id)
        items = await self.repo.get_by_servizio(
            servizio_id, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_by_servizio(servizio_id)
        responses = [RepertorioItemResponse.model_validate(i) for i in items]
        return paginate(responses, total, params)

    async def get_by_prova(
        self, prova_id: int, params: PageParams
    ) -> PagedResponse[RepertorioItemResponse]:
        prova = await self.prova_repo.get_by_id(prova_id)
        if not prova:
            raise ProvaNotFoundError(prova_id)
        items = await self.repo.get_by_prova(
            prova_id, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_by_prova(prova_id)
        responses = [RepertorioItemResponse.model_validate(i) for i in items]
        return paginate(responses, total, params)

    async def get_by_id(self, repertorio_item_id: int) -> RepertorioItemResponse:
        item = await self.repo.get_by_id(repertorio_item_id)
        if not item:
            raise RepertorioItemNotFoundError(repertorio_item_id)
        return RepertorioItemResponse.model_validate(item)

    async def create(self, data: RepertorioItemCreate) -> RepertorioItemResponse:
        nome_parte = await self.nome_parte_repo.get_by_id(data.nome_parte_id)
        if not nome_parte:
            raise NomeParteNotFoundError(data.nome_parte_id)
        if data.servizio_id is not None:
            servizio = await self.servizio_repo.get_by_id(data.servizio_id)
            if not servizio:
                raise ServizioNotFoundError(data.servizio_id)
        else:
            assert data.prova_id is not None
            prova = await self.prova_repo.get_by_id(data.prova_id)
            if not prova:
                raise ProvaNotFoundError(data.prova_id)
        item = await self.repo.create(data)
        return RepertorioItemResponse.model_validate(item)

    async def update(
        self, repertorio_item_id: int, data: RepertorioItemUpdate
    ) -> RepertorioItemResponse:
        item = await self.repo.get_by_id(repertorio_item_id)
        if not item:
            raise RepertorioItemNotFoundError(repertorio_item_id)
        updated = await self.repo.update(item, data)
        return RepertorioItemResponse.model_validate(updated)

    async def delete(self, repertorio_item_id: int) -> None:
        item = await self.repo.get_by_id(repertorio_item_id)
        if not item:
            raise RepertorioItemNotFoundError(repertorio_item_id)
        await self.repo.delete(item)
