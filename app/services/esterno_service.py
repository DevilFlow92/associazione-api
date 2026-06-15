from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.esterno import EsternoDuplicateCodiceError, EsternoNotFoundError
from app.exceptions.persona import PersonaNotFoundError
from app.repositories.esterno_repository import EsternoRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.esterno import EsternoCreate, EsternoResponse, EsternoUpdate


class EsternoService:
    def __init__(
        self, repo: EsternoRepository, persona_repo: PersonaRepository
    ) -> None:
        self.repo = repo
        self.persona_repo = persona_repo

    async def get_all(self, params: PageParams) -> PagedResponse[EsternoResponse]:
        esterni = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [EsternoResponse.model_validate(e) for e in esterni]
        return paginate(items, total, params)

    async def get_by_id(self, esterno_id: int) -> EsternoResponse:
        esterno = await self.repo.get_by_id(esterno_id)
        if not esterno:
            raise EsternoNotFoundError(esterno_id)
        return EsternoResponse.model_validate(esterno)

    async def create(self, data: EsternoCreate) -> EsternoResponse:
        persona = await self.persona_repo.get_by_id(data.persona_id)
        if not persona:
            raise PersonaNotFoundError(data.persona_id)
        existing = await self.repo.get_by_codice(data.codice_esterno)
        if existing:
            raise EsternoDuplicateCodiceError(data.codice_esterno)
        esterno = await self.repo.create(data)
        return EsternoResponse.model_validate(esterno)

    async def update(self, esterno_id: int, data: EsternoUpdate) -> EsternoResponse:
        esterno = await self.repo.get_by_id(esterno_id)
        if not esterno:
            raise EsternoNotFoundError(esterno_id)
        if data.codice_esterno and data.codice_esterno != esterno.codice_esterno:
            existing = await self.repo.get_by_codice(data.codice_esterno)
            if existing and existing.id != esterno_id:
                raise EsternoDuplicateCodiceError(data.codice_esterno)
        updated = await self.repo.update(esterno, data)
        return EsternoResponse.model_validate(updated)

    async def delete(self, esterno_id: int) -> None:
        esterno = await self.repo.get_by_id(esterno_id)
        if not esterno:
            raise EsternoNotFoundError(esterno_id)
        await self.repo.delete(esterno)
