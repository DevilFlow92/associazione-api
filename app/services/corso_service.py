from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.corso import CorsoNotFoundError
from app.exceptions.lookup import LookupNotFoundError
from app.exceptions.persona import PersonaNotFoundError
from app.models.lookups import TipoCorso
from app.repositories.corso_repository import CorsoRepository
from app.repositories.lookup import LookupRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.corso import CorsoCreate, CorsoResponse, CorsoUpdate


class CorsoService:
    def __init__(
        self,
        repo: CorsoRepository,
        tipo_corso_repo: LookupRepository[TipoCorso],
        persona_repo: PersonaRepository,
    ) -> None:
        self.repo = repo
        self.tipo_corso_repo = tipo_corso_repo
        self.persona_repo = persona_repo

    async def _check_fk(self, data: CorsoCreate | CorsoUpdate) -> None:
        if data.tipo_corso_codice is not None:
            tipo_corso = await self.tipo_corso_repo.get_by_codice(
                data.tipo_corso_codice
            )
            if not tipo_corso:
                raise LookupNotFoundError("Tipo corso", data.tipo_corso_codice)
        if data.coordinatore_persona_id is not None:
            coordinatore = await self.persona_repo.get_by_id(
                data.coordinatore_persona_id
            )
            if not coordinatore:
                raise PersonaNotFoundError(data.coordinatore_persona_id)
        if data.insegnante_persona_id is not None:
            insegnante = await self.persona_repo.get_by_id(data.insegnante_persona_id)
            if not insegnante:
                raise PersonaNotFoundError(data.insegnante_persona_id)

    async def get_all(
        self,
        params: PageParams,
        banda_codice: int | None = None,
        anno: int | None = None,
        tipo_corso_codice: int | None = None,
    ) -> PagedResponse[CorsoResponse]:
        corsi = await self.repo.get_all(
            banda_codice=banda_codice,
            anno=anno,
            tipo_corso_codice=tipo_corso_codice,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(
            banda_codice=banda_codice, anno=anno, tipo_corso_codice=tipo_corso_codice
        )
        items = [CorsoResponse.model_validate(c) for c in corsi]
        return paginate(items, total, params)

    async def get_by_id(self, corso_id: int) -> CorsoResponse:
        corso = await self.repo.get_by_id(corso_id)
        if not corso:
            raise CorsoNotFoundError(corso_id)
        return CorsoResponse.model_validate(corso)

    async def create(self, data: CorsoCreate) -> CorsoResponse:
        await self._check_fk(data)
        corso = await self.repo.create(data)
        return CorsoResponse.model_validate(corso)

    async def update(self, corso_id: int, data: CorsoUpdate) -> CorsoResponse:
        corso = await self.repo.get_by_id(corso_id)
        if not corso:
            raise CorsoNotFoundError(corso_id)
        await self._check_fk(data)
        updated = await self.repo.update(corso, data)
        return CorsoResponse.model_validate(updated)

    async def delete(self, corso_id: int) -> None:
        corso = await self.repo.get_by_id(corso_id)
        if not corso:
            raise CorsoNotFoundError(corso_id)
        await self.repo.delete(corso)
