from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.exceptions.servizio import ServizioHasRicevuteError, ServizioNotFoundError
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.servizio import ServizioCreate, ServizioResponse, ServizioUpdate


class ServizioService:
    def __init__(
        self, repo: ServizioRepository, indirizzo_repo: IndirizzoRepository
    ) -> None:
        self.repo = repo
        self.indirizzo_repo = indirizzo_repo

    async def get_all(
        self,
        anno: int | None,
        params: PageParams,
        banda_codice: int | None = None,
    ) -> PagedResponse[ServizioResponse]:
        servizi = await self.repo.get_all(
            anno=anno,
            banda_codice=banda_codice,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(anno=anno, banda_codice=banda_codice)
        items = [ServizioResponse.model_validate(s) for s in servizi]
        return paginate(items, total, params)

    async def get_by_id(self, servizio_id: int) -> ServizioResponse:
        servizio = await self.repo.get_by_id(servizio_id)
        if not servizio:
            raise ServizioNotFoundError(servizio_id)
        return ServizioResponse.model_validate(servizio)

    async def create(self, data: ServizioCreate) -> ServizioResponse:
        indirizzo = await self.indirizzo_repo.get_by_id(data.indirizzo_id)
        if not indirizzo:
            raise IndirizzoNotFoundError(data.indirizzo_id)
        servizio = await self.repo.create(data)
        return ServizioResponse.model_validate(servizio)

    async def update(self, servizio_id: int, data: ServizioUpdate) -> ServizioResponse:
        servizio = await self.repo.get_by_id(servizio_id)
        if not servizio:
            raise ServizioNotFoundError(servizio_id)
        if data.indirizzo_id is not None:
            indirizzo = await self.indirizzo_repo.get_by_id(data.indirizzo_id)
            if not indirizzo:
                raise IndirizzoNotFoundError(data.indirizzo_id)
        updated = await self.repo.update(servizio, data)
        return ServizioResponse.model_validate(updated)

    async def delete(self, servizio_id: int) -> None:
        servizio = await self.repo.get_by_id(servizio_id)
        if not servizio:
            raise ServizioNotFoundError(servizio_id)
        if await self.repo.has_ricevute(servizio_id):
            raise ServizioHasRicevuteError(servizio_id)
        await self.repo.delete(servizio)
