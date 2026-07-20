from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.persona import PersonaNotFoundError
from app.exceptions.ricevuta import RicevutaNotFoundError
from app.exceptions.servizio import ServizioNotFoundError
from app.repositories.persona_repository import PersonaRepository
from app.repositories.ricevuta_repository import RicevutaRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.ricevuta import RicevutaCreate, RicevutaResponse, RicevutaUpdate


class RicevutaService:
    def __init__(
        self,
        repo: RicevutaRepository,
        servizio_repo: ServizioRepository,
        persona_repo: PersonaRepository,
    ) -> None:
        self.repo = repo
        self.servizio_repo = servizio_repo
        self.persona_repo = persona_repo

    async def get_all(self, params: PageParams) -> PagedResponse[RicevutaResponse]:
        ricevute = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [RicevutaResponse.model_validate(r) for r in ricevute]
        return paginate(items, total, params)

    async def get_by_servizio(
        self, servizio_id: int, params: PageParams
    ) -> PagedResponse[RicevutaResponse]:
        servizio = await self.servizio_repo.get_by_id(servizio_id)
        if not servizio:
            raise ServizioNotFoundError(servizio_id)
        ricevute = await self.repo.get_by_servizio(
            servizio_id, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_by_servizio(servizio_id)
        items = [RicevutaResponse.model_validate(r) for r in ricevute]
        return paginate(items, total, params)

    async def get_by_id(self, ricevuta_id: int) -> RicevutaResponse:
        ricevuta = await self.repo.get_by_id(ricevuta_id)
        if not ricevuta:
            raise RicevutaNotFoundError(ricevuta_id)
        return RicevutaResponse.model_validate(ricevuta)

    async def create(self, data: RicevutaCreate) -> RicevutaResponse:
        # servizio/persona sono opzionali: una ricevuta può riguardare un
        # servizio (compenso a un socio o un esterno) oppure una quota di
        # iscrizione (collegata dall'iscrizione). Validati solo se forniti.
        if data.servizio_id is not None:
            servizio = await self.servizio_repo.get_by_id(data.servizio_id)
            if not servizio:
                raise ServizioNotFoundError(data.servizio_id)
        if data.persona_id is not None:
            persona = await self.persona_repo.get_by_id(data.persona_id)
            if not persona:
                raise PersonaNotFoundError(data.persona_id)
        ricevuta = await self.repo.create(data)
        return RicevutaResponse.model_validate(ricevuta)

    async def update(self, ricevuta_id: int, data: RicevutaUpdate) -> RicevutaResponse:
        ricevuta = await self.repo.get_by_id(ricevuta_id)
        if not ricevuta:
            raise RicevutaNotFoundError(ricevuta_id)
        updated = await self.repo.update(ricevuta, data)
        return RicevutaResponse.model_validate(updated)

    async def delete(self, ricevuta_id: int) -> None:
        ricevuta = await self.repo.get_by_id(ricevuta_id)
        if not ricevuta:
            raise RicevutaNotFoundError(ricevuta_id)
        await self.repo.delete(ricevuta)
