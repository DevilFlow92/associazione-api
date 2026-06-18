from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.exceptions.persona import PersonaHasDependentsError, PersonaNotFoundError
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.indirizzo import IndirizzoResponse
from app.schemas.persona import PersonaCreate, PersonaResponse, PersonaUpdate


class PersonaService:
    def __init__(
        self, repo: PersonaRepository, indirizzo_repo: IndirizzoRepository
    ) -> None:
        self.repo = repo
        self.indirizzo_repo = indirizzo_repo

    async def get_all(
        self, params: PageParams, banda_codice: int | None = None
    ) -> PagedResponse[PersonaResponse]:
        persone = await self.repo.get_all(
            offset=params.offset, limit=params.limit, banda_codice=banda_codice
        )
        total = await self.repo.count_all(banda_codice=banda_codice)
        items = [PersonaResponse.model_validate(p) for p in persone]
        return paginate(items, total, params)

    async def get_by_id(self, persona_id: int) -> PersonaResponse:
        persona = await self.repo.get_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(persona_id)
        return PersonaResponse.model_validate(persona)

    async def create(self, data: PersonaCreate) -> PersonaResponse:
        persona = await self.repo.create(data)
        return PersonaResponse.model_validate(persona)

    async def update(self, persona_id: int, data: PersonaUpdate) -> PersonaResponse:
        persona = await self.repo.get_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(persona_id)
        updated = await self.repo.update(persona, data)
        return PersonaResponse.model_validate(updated)

    async def delete(self, persona_id: int) -> None:
        persona = await self.repo.get_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(persona_id)
        if await self.repo.has_dependents(persona_id):
            raise PersonaHasDependentsError(persona_id)
        await self.repo.delete(persona_id)

    # ── Indirizzi (relazione molti-a-molti) ──────────────────────────────────
    async def get_indirizzi(self, persona_id: int) -> list[IndirizzoResponse]:
        persona = await self.repo.get_with_indirizzi(persona_id)
        if not persona:
            raise PersonaNotFoundError(persona_id)
        return [IndirizzoResponse.model_validate(i) for i in persona.indirizzi]

    async def add_indirizzo(
        self, persona_id: int, indirizzo_id: int
    ) -> list[IndirizzoResponse]:
        persona = await self.repo.get_with_indirizzi(persona_id)
        if not persona:
            raise PersonaNotFoundError(persona_id)
        indirizzo = await self.indirizzo_repo.get_by_id(indirizzo_id)
        if not indirizzo:
            raise IndirizzoNotFoundError(indirizzo_id)
        await self.repo.add_indirizzo(persona, indirizzo)
        return [IndirizzoResponse.model_validate(i) for i in persona.indirizzi]

    async def remove_indirizzo(self, persona_id: int, indirizzo_id: int) -> None:
        persona = await self.repo.get_with_indirizzi(persona_id)
        if not persona:
            raise PersonaNotFoundError(persona_id)
        indirizzo = await self.indirizzo_repo.get_by_id(indirizzo_id)
        if not indirizzo:
            raise IndirizzoNotFoundError(indirizzo_id)
        await self.repo.remove_indirizzo(persona, indirizzo)
