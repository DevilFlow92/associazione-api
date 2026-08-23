from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.lookup import LookupNotFoundError
from app.exceptions.voce_programma_catalogo import (
    VoceProgrammaCatalogoDuplicataError,
    VoceProgrammaCatalogoNotFoundError,
)
from app.models.lookups import CategoriaVoceProgramma, TipoCorso
from app.repositories.lookup import LookupRepository
from app.repositories.voce_programma_catalogo_repository import (
    VoceProgrammaCatalogoRepository,
)
from app.schemas.voce_programma_catalogo import (
    VoceProgrammaCatalogoCreate,
    VoceProgrammaCatalogoResponse,
    VoceProgrammaCatalogoUpdate,
)


class VoceProgrammaCatalogoService:
    def __init__(
        self,
        repo: VoceProgrammaCatalogoRepository,
        tipo_corso_repo: LookupRepository[TipoCorso],
        categoria_repo: LookupRepository[CategoriaVoceProgramma],
    ) -> None:
        self.repo = repo
        self.tipo_corso_repo = tipo_corso_repo
        self.categoria_repo = categoria_repo

    async def get_all(
        self,
        params: PageParams,
        tipo_corso_codice: int | None = None,
        categoria_codice: int | None = None,
        livello: int | None = None,
        attiva: bool | None = None,
    ) -> PagedResponse[VoceProgrammaCatalogoResponse]:
        voci = await self.repo.get_all(
            tipo_corso_codice=tipo_corso_codice,
            categoria_codice=categoria_codice,
            livello=livello,
            attiva=attiva,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(
            tipo_corso_codice=tipo_corso_codice,
            categoria_codice=categoria_codice,
            livello=livello,
            attiva=attiva,
        )
        items = [VoceProgrammaCatalogoResponse.model_validate(v) for v in voci]
        return paginate(items, total, params)

    async def get_by_id(self, voce_id: int) -> VoceProgrammaCatalogoResponse:
        voce = await self.repo.get_by_id(voce_id)
        if not voce:
            raise VoceProgrammaCatalogoNotFoundError(voce_id)
        return VoceProgrammaCatalogoResponse.model_validate(voce)

    async def create(
        self, data: VoceProgrammaCatalogoCreate
    ) -> VoceProgrammaCatalogoResponse:
        tipo_corso = await self.tipo_corso_repo.get_by_codice(data.tipo_corso_codice)
        if not tipo_corso:
            raise LookupNotFoundError("Tipo corso", data.tipo_corso_codice)
        categoria = await self.categoria_repo.get_by_codice(data.categoria_codice)
        if not categoria:
            raise LookupNotFoundError("Categoria voce programma", data.categoria_codice)
        existing = await self.repo.get_by_tipo_corso_e_testo(
            data.tipo_corso_codice, data.testo
        )
        if existing:
            raise VoceProgrammaCatalogoDuplicataError(
                data.tipo_corso_codice, data.testo
            )
        voce = await self.repo.create(data)
        return VoceProgrammaCatalogoResponse.model_validate(voce)

    async def update(
        self, voce_id: int, data: VoceProgrammaCatalogoUpdate
    ) -> VoceProgrammaCatalogoResponse:
        voce = await self.repo.get_by_id(voce_id)
        if not voce:
            raise VoceProgrammaCatalogoNotFoundError(voce_id)
        if data.testo is not None and data.testo != voce.testo:
            existing = await self.repo.get_by_tipo_corso_e_testo(
                voce.tipo_corso_codice, data.testo
            )
            if existing:
                raise VoceProgrammaCatalogoDuplicataError(
                    voce.tipo_corso_codice, data.testo
                )
        updated = await self.repo.update(voce, data)
        return VoceProgrammaCatalogoResponse.model_validate(updated)
