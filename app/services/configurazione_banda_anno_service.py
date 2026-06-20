from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.configurazione_banda_anno import (
    ConfigurazioneBandaAnnoChiusaError,
    ConfigurazioneBandaAnnoDuplicateError,
    ConfigurazioneBandaAnnoNotFoundError,
)
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.schemas.configurazione_banda_anno import (
    ConfigurazioneBandaAnnoCreate,
    ConfigurazioneBandaAnnoResponse,
    ConfigurazioneBandaAnnoUpdate,
)


class ConfigurazioneBandaAnnoService:
    def __init__(self, repo: ConfigurazioneBandaAnnoRepository) -> None:
        self.repo = repo

    async def get_all(
        self,
        banda_codice: int | None,
        anno: int | None,
        params: PageParams,
    ) -> PagedResponse[ConfigurazioneBandaAnnoResponse]:
        items = await self.repo.get_all(
            banda_codice=banda_codice,
            anno=anno,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(banda_codice=banda_codice, anno=anno)
        return paginate(
            [ConfigurazioneBandaAnnoResponse.model_validate(c) for c in items],
            total,
            params,
        )

    async def get_by_id(self, cfg_id: int) -> ConfigurazioneBandaAnnoResponse:
        cfg = await self.repo.get_by_id(cfg_id)
        if not cfg:
            raise ConfigurazioneBandaAnnoNotFoundError(cfg_id)
        return ConfigurazioneBandaAnnoResponse.model_validate(cfg)

    async def get_by_banda_anno(
        self, banda_codice: int, anno: int
    ) -> ConfigurazioneBandaAnnoResponse:
        cfg = await self.repo.get_by_banda_anno(banda_codice, anno)
        if not cfg:
            raise ConfigurazioneBandaAnnoNotFoundError(-1)
        return ConfigurazioneBandaAnnoResponse.model_validate(cfg)

    async def create(
        self, data: ConfigurazioneBandaAnnoCreate
    ) -> ConfigurazioneBandaAnnoResponse:
        if await self.repo.exists_by_banda_anno(data.banda_codice, data.anno):
            raise ConfigurazioneBandaAnnoDuplicateError(data.banda_codice, data.anno)
        cfg = await self.repo.create(data)
        return ConfigurazioneBandaAnnoResponse.model_validate(cfg)

    async def update(
        self, cfg_id: int, data: ConfigurazioneBandaAnnoUpdate
    ) -> ConfigurazioneBandaAnnoResponse:
        cfg = await self.repo.get_by_id(cfg_id)
        if not cfg:
            raise ConfigurazioneBandaAnnoNotFoundError(cfg_id)
        if cfg.chiuso:
            raise ConfigurazioneBandaAnnoChiusaError(cfg_id)
        updated = await self.repo.update(cfg, data)
        return ConfigurazioneBandaAnnoResponse.model_validate(updated)

    async def delete(self, cfg_id: int) -> None:
        cfg = await self.repo.get_by_id(cfg_id)
        if not cfg:
            raise ConfigurazioneBandaAnnoNotFoundError(cfg_id)
        if cfg.chiuso:
            raise ConfigurazioneBandaAnnoChiusaError(cfg_id)
        await self.repo.delete(cfg)
