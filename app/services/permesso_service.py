from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.repositories.permesso_repository import PermessoRepository
from app.schemas.permesso import PermessoResponse


class PermessoService:
    def __init__(self, repo: PermessoRepository) -> None:
        self.repo = repo

    async def get_all(self, params: PageParams) -> PagedResponse[PermessoResponse]:
        permessi = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [PermessoResponse.model_validate(p) for p in permessi]
        return paginate(items, total, params)
