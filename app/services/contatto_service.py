from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.contatto import ContattoNotFoundError
from app.exceptions.persona import PersonaNotFoundError
from app.repositories.contatto_repository import ContattoRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.contatto import ContattoCreate, ContattoResponse, ContattoUpdate


class ContattoService:
    def __init__(
        self, repo: ContattoRepository, persona_repo: PersonaRepository
    ) -> None:
        self.repo = repo
        self.persona_repo = persona_repo

    async def get_by_persona(
        self, persona_id: int, params: PageParams
    ) -> PagedResponse[ContattoResponse]:
        persona = await self.persona_repo.get_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(persona_id)
        contatti = await self.repo.get_by_persona(
            persona_id, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_by_persona(persona_id)
        items = [ContattoResponse.model_validate(c) for c in contatti]
        return paginate(items, total, params)

    async def get_by_id(self, contatto_id: int) -> ContattoResponse:
        contatto = await self.repo.get_by_id(contatto_id)
        if not contatto:
            raise ContattoNotFoundError(contatto_id)
        return ContattoResponse.model_validate(contatto)

    async def create(self, data: ContattoCreate) -> ContattoResponse:
        persona = await self.persona_repo.get_by_id(data.persona_id)
        if not persona:
            raise PersonaNotFoundError(data.persona_id)
        contatto = await self.repo.create(data)
        return ContattoResponse.model_validate(contatto)

    async def update(self, contatto_id: int, data: ContattoUpdate) -> ContattoResponse:
        contatto = await self.repo.get_by_id(contatto_id)
        if not contatto:
            raise ContattoNotFoundError(contatto_id)
        updated = await self.repo.update(contatto, data)
        return ContattoResponse.model_validate(updated)

    async def delete(self, contatto_id: int) -> None:
        contatto = await self.repo.get_by_id(contatto_id)
        if not contatto:
            raise ContattoNotFoundError(contatto_id)
        await self.repo.delete(contatto)
