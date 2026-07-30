from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.corso import CorsoNotFoundError
from app.exceptions.documento import DocumentoNotFoundError
from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.lookup import LookupNotFoundError
from app.exceptions.persona import PersonaNotFoundError
from app.models.lookups import StatoIscrizioneCorso
from app.repositories.corso_repository import CorsoRepository
from app.repositories.documento_repository import DocumentoRepository
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.lookup import LookupRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.iscrizione_corso import (
    IscrizioneCorsoCreate,
    IscrizioneCorsoResponse,
    IscrizioneCorsoUpdate,
)


class IscrizioneCorsoService:
    def __init__(
        self,
        repo: IscrizioneCorsoRepository,
        corso_repo: CorsoRepository,
        persona_repo: PersonaRepository,
        stato_repo: LookupRepository[StatoIscrizioneCorso],
        documento_repo: DocumentoRepository,
    ) -> None:
        self.repo = repo
        self.corso_repo = corso_repo
        self.persona_repo = persona_repo
        self.stato_repo = stato_repo
        self.documento_repo = documento_repo

    async def _check_fk(
        self, data: IscrizioneCorsoCreate | IscrizioneCorsoUpdate
    ) -> None:
        if data.corso_id is not None:
            corso = await self.corso_repo.get_by_id(data.corso_id)
            if not corso:
                raise CorsoNotFoundError(data.corso_id)
        if data.persona_id is not None:
            persona = await self.persona_repo.get_by_id(data.persona_id)
            if not persona:
                raise PersonaNotFoundError(data.persona_id)
        if data.stato_iscrizione_corso_codice is not None:
            stato = await self.stato_repo.get_by_codice(
                data.stato_iscrizione_corso_codice
            )
            if not stato:
                raise LookupNotFoundError(
                    "Stato iscrizione corso", data.stato_iscrizione_corso_codice
                )
        if data.documento_id is not None:
            documento = await self.documento_repo.get_by_id(data.documento_id)
            if not documento:
                raise DocumentoNotFoundError(data.documento_id)

    async def get_all(
        self,
        params: PageParams,
        corso_id: int | None = None,
        persona_id: int | None = None,
    ) -> PagedResponse[IscrizioneCorsoResponse]:
        iscrizioni = await self.repo.get_all(
            corso_id=corso_id,
            persona_id=persona_id,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(corso_id=corso_id, persona_id=persona_id)
        items = [IscrizioneCorsoResponse.model_validate(i) for i in iscrizioni]
        return paginate(items, total, params)

    async def get_by_id(self, iscrizione_corso_id: int) -> IscrizioneCorsoResponse:
        iscrizione_corso = await self.repo.get_by_id(iscrizione_corso_id)
        if not iscrizione_corso:
            raise IscrizioneCorsoNotFoundError(iscrizione_corso_id)
        return IscrizioneCorsoResponse.model_validate(iscrizione_corso)

    async def create(self, data: IscrizioneCorsoCreate) -> IscrizioneCorsoResponse:
        await self._check_fk(data)
        iscrizione_corso = await self.repo.create(data)
        return IscrizioneCorsoResponse.model_validate(iscrizione_corso)

    async def update(
        self, iscrizione_corso_id: int, data: IscrizioneCorsoUpdate
    ) -> IscrizioneCorsoResponse:
        iscrizione_corso = await self.repo.get_by_id(iscrizione_corso_id)
        if not iscrizione_corso:
            raise IscrizioneCorsoNotFoundError(iscrizione_corso_id)
        await self._check_fk(data)
        updated = await self.repo.update(iscrizione_corso, data)
        return IscrizioneCorsoResponse.model_validate(updated)

    async def delete(self, iscrizione_corso_id: int) -> None:
        iscrizione_corso = await self.repo.get_by_id(iscrizione_corso_id)
        if not iscrizione_corso:
            raise IscrizioneCorsoNotFoundError(iscrizione_corso_id)
        await self.repo.delete(iscrizione_corso)
