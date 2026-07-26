from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.exceptions.prova import ProvaNotFoundError
from app.exceptions.servizio import ServizioNotFoundError
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.prova import ProvaCreate, ProvaResponse, ProvaUpdate


class ProvaService:
    def __init__(
        self,
        repo: ProvaRepository,
        indirizzo_repo: IndirizzoRepository,
        servizio_repo: ServizioRepository,
    ) -> None:
        self.repo = repo
        self.indirizzo_repo = indirizzo_repo
        self.servizio_repo = servizio_repo

    async def get_all(
        self,
        params: PageParams,
        banda_codice: int | None = None,
        servizio_id: int | None = None,
    ) -> PagedResponse[ProvaResponse]:
        prove = await self.repo.get_all(
            banda_codice=banda_codice,
            servizio_id=servizio_id,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(
            banda_codice=banda_codice, servizio_id=servizio_id
        )
        items = [ProvaResponse.model_validate(p) for p in prove]
        return paginate(items, total, params)

    async def get_by_id(self, prova_id: int) -> ProvaResponse:
        prova = await self.repo.get_by_id(prova_id)
        if not prova:
            raise ProvaNotFoundError(prova_id)
        return ProvaResponse.model_validate(prova)

    async def create(self, data: ProvaCreate) -> ProvaResponse:
        if data.indirizzo_id is not None:
            indirizzo = await self.indirizzo_repo.get_by_id(data.indirizzo_id)
            if not indirizzo:
                raise IndirizzoNotFoundError(data.indirizzo_id)
        if data.servizio_id is not None:
            servizio = await self.servizio_repo.get_by_id(data.servizio_id)
            if not servizio:
                raise ServizioNotFoundError(data.servizio_id)
        prova = await self.repo.create(data)
        return ProvaResponse.model_validate(prova)

    async def update(self, prova_id: int, data: ProvaUpdate) -> ProvaResponse:
        prova = await self.repo.get_by_id(prova_id)
        if not prova:
            raise ProvaNotFoundError(prova_id)
        if data.indirizzo_id is not None:
            indirizzo = await self.indirizzo_repo.get_by_id(data.indirizzo_id)
            if not indirizzo:
                raise IndirizzoNotFoundError(data.indirizzo_id)
        if data.servizio_id is not None:
            servizio = await self.servizio_repo.get_by_id(data.servizio_id)
            if not servizio:
                raise ServizioNotFoundError(data.servizio_id)
        updated = await self.repo.update(prova, data)
        return ProvaResponse.model_validate(updated)

    async def delete(self, prova_id: int) -> None:
        prova = await self.repo.get_by_id(prova_id)
        if not prova:
            raise ProvaNotFoundError(prova_id)
        await self.repo.delete(prova)
