from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.spartito import NomeParteNotFoundError
from app.repositories.nome_parte_repository import NomeParteRepository
from app.schemas.spartito import NomeParteCreate, NomeParteResponse, NomeParteUpdate


class NomeParteService:
    def __init__(self, repo: NomeParteRepository) -> None:
        self.repo = repo

    async def get_all(
        self,
        banda_codice: int,
        tipo_spartito_codice: int | None,
        params: PageParams,
    ) -> PagedResponse[NomeParteResponse]:
        items = await self.repo.get_all(
            banda_codice=banda_codice,
            tipo_spartito_codice=tipo_spartito_codice,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(
            banda_codice=banda_codice,
            tipo_spartito_codice=tipo_spartito_codice,
        )
        responses = []
        for np in items:
            r = NomeParteResponse.model_validate(np)
            r.num_parti = len(np.spartiti)
            responses.append(r)
        return paginate(responses, total, params)

    async def get_by_id(self, id: int) -> NomeParteResponse:
        obj = await self.repo.get_by_id(id)
        if not obj:
            raise NomeParteNotFoundError(id)
        r = NomeParteResponse.model_validate(obj)
        r.num_parti = len(obj.spartiti)
        return r

    async def create(self, data: NomeParteCreate) -> NomeParteResponse:
        obj = await self.repo.create(data)
        r = NomeParteResponse.model_validate(obj)
        r.num_parti = 0
        return r

    async def update(self, id: int, data: NomeParteUpdate) -> NomeParteResponse:
        obj = await self.repo.get_by_id(id)
        if not obj:
            raise NomeParteNotFoundError(id)
        updated = await self.repo.update(obj, data)
        r = NomeParteResponse.model_validate(updated)
        r.num_parti = len(updated.spartiti)
        return r

    async def delete(self, id: int) -> None:
        obj = await self.repo.get_by_id(id)
        if not obj:
            raise NomeParteNotFoundError(id)
        await self.repo.delete(obj)
