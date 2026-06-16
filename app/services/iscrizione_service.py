from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.iscrizione import IscrizioneNotFoundError
from app.exceptions.socio import SocioNotFoundError
from app.repositories.iscrizione_repository import IscrizioneRepository
from app.repositories.socio_repository import SocioRepository
from app.schemas.iscrizione import (
    IscrizioneCreate,
    IscrizioneResponse,
    IscrizioneUpdate,
)


class IscrizioneService:
    def __init__(
        self,
        repo: IscrizioneRepository,
        socio_repo: SocioRepository,
    ) -> None:
        self.repo = repo
        self.socio_repo = socio_repo

    async def get_all(
        self,
        socio_id: int | None,
        anno: int | None,
        params: PageParams,
    ) -> PagedResponse[IscrizioneResponse]:
        iscrizioni = await self.repo.get_all(
            socio_id=socio_id, anno=anno, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_all(socio_id=socio_id, anno=anno)
        items = [IscrizioneResponse.model_validate(i) for i in iscrizioni]
        return paginate(items, total, params)

    async def get_by_id(self, iscrizione_id: int) -> IscrizioneResponse:
        iscrizione = await self.repo.get_by_id(iscrizione_id)
        if not iscrizione:
            raise IscrizioneNotFoundError(iscrizione_id)
        return IscrizioneResponse.model_validate(iscrizione)

    async def create(self, data: IscrizioneCreate) -> IscrizioneResponse:
        socio = await self.socio_repo.get_by_id(data.socio_id)
        if not socio:
            raise SocioNotFoundError(data.socio_id)
        # Doppia iscrizione (socio, anno) o altre FK invalide → 409 (handler globale).
        iscrizione = await self.repo.create(data)
        return IscrizioneResponse.model_validate(iscrizione)

    async def update(
        self, iscrizione_id: int, data: IscrizioneUpdate
    ) -> IscrizioneResponse:
        iscrizione = await self.repo.get_by_id(iscrizione_id)
        if not iscrizione:
            raise IscrizioneNotFoundError(iscrizione_id)
        updated = await self.repo.update(iscrizione, data)
        return IscrizioneResponse.model_validate(updated)

    async def delete(self, iscrizione_id: int) -> None:
        iscrizione = await self.repo.get_by_id(iscrizione_id)
        if not iscrizione:
            raise IscrizioneNotFoundError(iscrizione_id)
        await self.repo.delete(iscrizione)
