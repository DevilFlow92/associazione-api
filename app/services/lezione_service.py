from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.corso import CorsoNotFoundError
from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.exceptions.lezione import LezioneNotFoundError
from app.repositories.corso_repository import CorsoRepository
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.repositories.lezione_repository import LezioneRepository
from app.schemas.lezione import LezioneCreate, LezioneResponse, LezioneUpdate


class LezioneService:
    def __init__(
        self,
        repo: LezioneRepository,
        corso_repo: CorsoRepository,
        indirizzo_repo: IndirizzoRepository,
    ) -> None:
        self.repo = repo
        self.corso_repo = corso_repo
        self.indirizzo_repo = indirizzo_repo

    async def _check_fk(self, data: LezioneCreate | LezioneUpdate) -> None:
        if data.corso_id is not None:
            corso = await self.corso_repo.get_by_id(data.corso_id)
            if not corso:
                raise CorsoNotFoundError(data.corso_id)
        if data.indirizzo_id is not None:
            indirizzo = await self.indirizzo_repo.get_by_id(data.indirizzo_id)
            if not indirizzo:
                raise IndirizzoNotFoundError(data.indirizzo_id)

    async def get_all(
        self, params: PageParams, corso_id: int | None = None
    ) -> PagedResponse[LezioneResponse]:
        lezioni = await self.repo.get_all(
            corso_id=corso_id, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_all(corso_id=corso_id)
        items = [LezioneResponse.model_validate(lz) for lz in lezioni]
        return paginate(items, total, params)

    async def get_by_id(self, lezione_id: int) -> LezioneResponse:
        lezione = await self.repo.get_by_id(lezione_id)
        if not lezione:
            raise LezioneNotFoundError(lezione_id)
        return LezioneResponse.model_validate(lezione)

    async def create(self, data: LezioneCreate) -> LezioneResponse:
        await self._check_fk(data)
        lezione = await self.repo.create(data)
        return LezioneResponse.model_validate(lezione)

    async def update(self, lezione_id: int, data: LezioneUpdate) -> LezioneResponse:
        lezione = await self.repo.get_by_id(lezione_id)
        if not lezione:
            raise LezioneNotFoundError(lezione_id)
        await self._check_fk(data)
        updated = await self.repo.update(lezione, data)
        return LezioneResponse.model_validate(updated)

    async def delete(self, lezione_id: int) -> None:
        lezione = await self.repo.get_by_id(lezione_id)
        if not lezione:
            raise LezioneNotFoundError(lezione_id)
        await self.repo.delete(lezione)
