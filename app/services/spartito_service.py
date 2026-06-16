from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.spartito import SpartitoNotFoundError
from app.repositories.spartito_repository import SpartitoRepository
from app.schemas.spartito import SpartitoCreate, SpartitoResponse, SpartitoUpdate


class SpartitoService:
    def __init__(self, repo: SpartitoRepository) -> None:
        self.repo = repo

    async def get_all(
        self,
        tipo_spartito_codice: int | None,
        strumento_codice: int | None,
        params: PageParams,
    ) -> PagedResponse[SpartitoResponse]:
        spartiti = await self.repo.get_all(
            tipo_spartito_codice=tipo_spartito_codice,
            strumento_codice=strumento_codice,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(
            tipo_spartito_codice=tipo_spartito_codice,
            strumento_codice=strumento_codice,
        )
        items = [SpartitoResponse.model_validate(s) for s in spartiti]
        return paginate(items, total, params)

    async def get_by_id(self, spartito_id: int) -> SpartitoResponse:
        spartito = await self.repo.get_by_id(spartito_id)
        if not spartito:
            raise SpartitoNotFoundError(spartito_id)
        return SpartitoResponse.model_validate(spartito)

    async def create(self, data: SpartitoCreate) -> SpartitoResponse:
        # FK inesistenti (tipo_spartito/strumento/documento) → 409 (handler globale).
        spartito = await self.repo.create(data)
        return SpartitoResponse.model_validate(spartito)

    async def update(self, spartito_id: int, data: SpartitoUpdate) -> SpartitoResponse:
        spartito = await self.repo.get_by_id(spartito_id)
        if not spartito:
            raise SpartitoNotFoundError(spartito_id)
        updated = await self.repo.update(spartito, data)
        return SpartitoResponse.model_validate(updated)

    async def delete(self, spartito_id: int) -> None:
        spartito = await self.repo.get_by_id(spartito_id)
        if not spartito:
            raise SpartitoNotFoundError(spartito_id)
        await self.repo.delete(spartito)
