from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.committente import (
    CommittenteHasServiziError,
    CommittenteNotFoundError,
)
from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.repositories.committente_repository import CommittenteRepository
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.schemas.committente import (
    CommittenteCreate,
    CommittenteResponse,
    CommittenteUpdate,
)


class CommittenteService:
    def __init__(
        self, repo: CommittenteRepository, indirizzo_repo: IndirizzoRepository
    ) -> None:
        self.repo = repo
        self.indirizzo_repo = indirizzo_repo

    async def get_all(self, params: PageParams) -> PagedResponse[CommittenteResponse]:
        committenti = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [CommittenteResponse.model_validate(c) for c in committenti]
        return paginate(items, total, params)

    async def get_by_id(self, committente_id: int) -> CommittenteResponse:
        committente = await self.repo.get_by_id(committente_id)
        if not committente:
            raise CommittenteNotFoundError(committente_id)
        return CommittenteResponse.model_validate(committente)

    async def create(self, data: CommittenteCreate) -> CommittenteResponse:
        if data.indirizzo_id is not None:
            indirizzo = await self.indirizzo_repo.get_by_id(data.indirizzo_id)
            if not indirizzo:
                raise IndirizzoNotFoundError(data.indirizzo_id)
        committente = await self.repo.create(data)
        return CommittenteResponse.model_validate(committente)

    async def update(
        self, committente_id: int, data: CommittenteUpdate
    ) -> CommittenteResponse:
        committente = await self.repo.get_by_id(committente_id)
        if not committente:
            raise CommittenteNotFoundError(committente_id)
        if data.indirizzo_id is not None:
            indirizzo = await self.indirizzo_repo.get_by_id(data.indirizzo_id)
            if not indirizzo:
                raise IndirizzoNotFoundError(data.indirizzo_id)
        updated = await self.repo.update(committente, data)
        return CommittenteResponse.model_validate(updated)

    async def delete(self, committente_id: int) -> None:
        committente = await self.repo.get_by_id(committente_id)
        if not committente:
            raise CommittenteNotFoundError(committente_id)
        if await self.repo.has_servizi(committente_id):
            raise CommittenteHasServiziError(committente_id)
        await self.repo.delete(committente)
