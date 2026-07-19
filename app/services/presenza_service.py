from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.persona import PersonaNotFoundError
from app.exceptions.presenza import PresenzaNotFoundError
from app.exceptions.servizio import ServizioNotFoundError
from app.repositories.persona_repository import PersonaRepository
from app.repositories.presenza_repository import PresenzaRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.presenza import PresenzaCreate, PresenzaResponse, PresenzaUpdate


class PresenzaService:
    def __init__(
        self,
        repo: PresenzaRepository,
        persona_repo: PersonaRepository,
        servizio_repo: ServizioRepository,
    ) -> None:
        self.repo = repo
        self.persona_repo = persona_repo
        self.servizio_repo = servizio_repo

    async def get_by_servizio(
        self, servizio_id: int, params: PageParams
    ) -> PagedResponse[PresenzaResponse]:
        servizio = await self.servizio_repo.get_by_id(servizio_id)
        if not servizio:
            raise ServizioNotFoundError(servizio_id)
        presenze = await self.repo.get_by_servizio(
            servizio_id, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_by_servizio(servizio_id)
        items = [PresenzaResponse.model_validate(p) for p in presenze]
        return paginate(items, total, params)

    async def get_by_id(self, presenza_id: int) -> PresenzaResponse:
        presenza = await self.repo.get_by_id(presenza_id)
        if not presenza:
            raise PresenzaNotFoundError(presenza_id)
        return PresenzaResponse.model_validate(presenza)

    async def create(self, data: PresenzaCreate) -> PresenzaResponse:
        persona = await self.persona_repo.get_by_id(data.persona_id)
        if not persona:
            raise PersonaNotFoundError(data.persona_id)
        servizio = await self.servizio_repo.get_by_id(data.servizio_id)
        if not servizio:
            raise ServizioNotFoundError(data.servizio_id)
        presenza = await self.repo.create(data)
        return PresenzaResponse.model_validate(presenza)

    async def update(self, presenza_id: int, data: PresenzaUpdate) -> PresenzaResponse:
        presenza = await self.repo.get_by_id(presenza_id)
        if not presenza:
            raise PresenzaNotFoundError(presenza_id)
        updated = await self.repo.update(presenza, data)
        return PresenzaResponse.model_validate(updated)

    async def delete(self, presenza_id: int) -> None:
        presenza = await self.repo.get_by_id(presenza_id)
        if not presenza:
            raise PresenzaNotFoundError(presenza_id)
        await self.repo.delete(presenza)
