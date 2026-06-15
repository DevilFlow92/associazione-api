from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate
from pydantic import BaseModel as PydanticModel

from app.exceptions.lookup import LookupDuplicateCodiceError, LookupNotFoundError
from app.repositories.lookup import LookupRepository


class LookupService[ResponseT: PydanticModel]:
    """Business logic generica per le tabelle dimensione (lookup).

    Validazione del codice duplicato e dell'esistenza, condivise da tutte le
    tabelle ``D_*``. La ``response_model`` serializza l'entità e ``label``
    rende i messaggi d'errore leggibili (es. "Strumento", "Comune").
    """

    def __init__(
        self,
        repo: LookupRepository,
        response_model: type[ResponseT],
        label: str,
    ) -> None:
        self.repo = repo
        self.response_model = response_model
        self.label = label

    async def get_all(self, params: PageParams) -> PagedResponse[ResponseT]:
        voci = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [self.response_model.model_validate(v) for v in voci]
        return paginate(items, total, params)

    async def get_by_codice(self, codice: int) -> ResponseT:
        voce = await self.repo.get_by_codice(codice)
        if not voce:
            raise LookupNotFoundError(self.label, codice)
        return self.response_model.model_validate(voce)

    async def create(self, data: PydanticModel) -> ResponseT:
        codice: int = data.model_dump()["codice"]
        existing = await self.repo.get_by_codice(codice)
        if existing:
            raise LookupDuplicateCodiceError(self.label, codice)
        voce = await self.repo.create(data)
        return self.response_model.model_validate(voce)

    async def update(self, codice: int, data: PydanticModel) -> ResponseT:
        voce = await self.repo.get_by_codice(codice)
        if not voce:
            raise LookupNotFoundError(self.label, codice)
        updated = await self.repo.update(voce, data)
        return self.response_model.model_validate(updated)

    async def delete(self, codice: int) -> None:
        voce = await self.repo.get_by_codice(codice)
        if not voce:
            raise LookupNotFoundError(self.label, codice)
        await self.repo.delete(voce)
