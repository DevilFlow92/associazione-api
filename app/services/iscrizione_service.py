from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.iscrizione import IscrizioneDuplicataError, IscrizioneNotFoundError
from app.exceptions.socio import SocioNotFoundError
from app.repositories.iscrizione_repository import IscrizioneRepository
from app.repositories.socio_repository import SocioRepository
from app.schemas.iscrizione import (
    IscrizioneCreate,
    IscrizioneResponse,
    IscrizioneUpdate,
)


class IscrizioneService:
    def __init__(self, repo: IscrizioneRepository, socio_repo: SocioRepository) -> None:
        self.repo = repo
        self.socio_repo = socio_repo

    async def get_by_socio(
        self, socio_id: int, params: PageParams
    ) -> PagedResponse[IscrizioneResponse]:
        socio = await self.socio_repo.get_by_id(socio_id)
        if not socio:
            raise SocioNotFoundError(socio_id)
        iscrizioni = await self.repo.get_by_socio(
            socio_id, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_by_socio(socio_id)
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
        existing = await self.repo.get_by_socio_anno(data.socio_id, data.anno)
        if existing:
            raise IscrizioneDuplicataError(data.socio_id, data.anno)
        iscrizione = await self.repo.create(data)
        return IscrizioneResponse.model_validate(iscrizione)

    async def update(
        self,
        iscrizione_id: int,
        data: IscrizioneUpdate,
    ) -> IscrizioneResponse:
        iscrizione = await self.repo.get_by_id(iscrizione_id)
        if not iscrizione:
            raise IscrizioneNotFoundError(iscrizione_id)
        updated = await self.repo.update(iscrizione, data)
        return IscrizioneResponse.model_validate(updated)
