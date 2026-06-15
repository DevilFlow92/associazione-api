from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.schemas.indirizzo import IndirizzoCreate, IndirizzoResponse, IndirizzoUpdate


class IndirizzoService:
    def __init__(self, repo: IndirizzoRepository) -> None:
        self.repo = repo

    async def get_all(self, params: PageParams) -> PagedResponse[IndirizzoResponse]:
        indirizzi = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [IndirizzoResponse.model_validate(i) for i in indirizzi]
        return paginate(items, total, params)

    async def get_by_id(self, indirizzo_id: int) -> IndirizzoResponse:
        indirizzo = await self.repo.get_by_id(indirizzo_id)
        if not indirizzo:
            raise IndirizzoNotFoundError(indirizzo_id)
        return IndirizzoResponse.model_validate(indirizzo)

    async def create(self, data: IndirizzoCreate) -> IndirizzoResponse:
        indirizzo = await self.repo.create(data)
        return IndirizzoResponse.model_validate(indirizzo)

    async def update(
        self, indirizzo_id: int, data: IndirizzoUpdate
    ) -> IndirizzoResponse:
        indirizzo = await self.repo.get_by_id(indirizzo_id)
        if not indirizzo:
            raise IndirizzoNotFoundError(indirizzo_id)
        updated = await self.repo.update(indirizzo, data)
        return IndirizzoResponse.model_validate(updated)

    async def delete(self, indirizzo_id: int) -> None:
        indirizzo = await self.repo.get_by_id(indirizzo_id)
        if not indirizzo:
            raise IndirizzoNotFoundError(indirizzo_id)
        await self.repo.delete(indirizzo)
