from __future__ import annotations

from datetime import datetime

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.configurazione_banda_anno import (
    AnnoGiaApertoError,
    AnnoGiaChiusoError,
    ConfigurazioneBandaAnnoChiusaError,
    ConfigurazioneBandaAnnoDuplicateError,
    ConfigurazioneBandaAnnoNotFoundError,
    RendicontoLookupNotFoundError,
)
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.schemas.configurazione_banda_anno import (
    ConfigurazioneBandaAnnoCreate,
    ConfigurazioneBandaAnnoResponse,
    ConfigurazioneBandaAnnoUpdate,
)

# Minimum chart-of-accounts seeded for every new banda.
# Each tuple: (voce_name, sezione_desc, voce_desc, sottovoce_desc)
_SEED_VOCI: list[tuple[str, str, str, str]] = [
    (
        "Quote associative",
        "Entrate",
        "A) Entrate da attività di interesse generale",
        "1) Entrate da quote associative e apporti dei fondatori",
    ),
    (
        "Saldo iniziale",
        "Fuori Bilancio",
        "Fuori Bilancio",
        "Fuori Bilancio",
    ),
    (
        "Versamento in banca",
        "Fuori Bilancio",
        "Fuori Bilancio",
        "Fuori Bilancio",
    ),
    (
        "Spese bancarie",
        "Uscite",
        "D) Uscite da attività finanziarie e patrimoniali",
        "1) Su rapporti bancari",
    ),
]


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

    async def _seed_minimum_voci(self, banda_codice: int) -> None:
        """Insert the minimum chart-of-accounts for a banda if none exist yet.

        Looks up sezione/voce/sottovoce codes by descrizione at runtime so the
        seed is resilient to lookup-table data changes. Raises
        RendicontoLookupNotFoundError if any required descrizione is missing.
        All inserts are staged without committing — they'll be committed
        atomically with the ConfigurazioneBandaAnno row.
        """
        if await self.repo.count_voci_contabilita(banda_codice) > 0:
            return

        for voce_name, sez_desc, voce_desc, sottovoce_desc in _SEED_VOCI:
            sezione_codice = await self.repo.lookup_sezione_codice(sez_desc)
            if sezione_codice is None:
                raise RendicontoLookupNotFoundError("sezioni_rendiconto", sez_desc)

            voce_codice = await self.repo.lookup_voce_codice(voce_desc)
            if voce_codice is None:
                raise RendicontoLookupNotFoundError("voci_rendiconto", voce_desc)

            sottovoce_codice = await self.repo.lookup_sottovoce_codice(sottovoce_desc)
            if sottovoce_codice is None:
                raise RendicontoLookupNotFoundError(
                    "sottovoci_rendiconto", sottovoce_desc
                )

            self.repo.add_voce_no_commit(
                banda_codice=banda_codice,
                voce_contabilita=voce_name,
                sezione_rendiconto_codice=sezione_codice,
                voce_rendiconto_codice=voce_codice,
                sottovoce_rendiconto_codice=sottovoce_codice,
            )

    async def create(
        self, data: ConfigurazioneBandaAnnoCreate
    ) -> ConfigurazioneBandaAnnoResponse:
        if await self.repo.exists_by_banda_anno(data.banda_codice, data.anno):
            raise ConfigurazioneBandaAnnoDuplicateError(data.banda_codice, data.anno)
        await self._seed_minimum_voci(data.banda_codice)
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

    async def chiudi_anno(
        self, cfg_id: int, utente_id: int
    ) -> ConfigurazioneBandaAnnoResponse:
        cfg = await self.repo.get_by_id(cfg_id)
        if not cfg:
            raise ConfigurazioneBandaAnnoNotFoundError(cfg_id)
        if cfg.chiuso:
            raise AnnoGiaChiusoError(cfg_id)
        updated = await self.repo.set_chiusura(
            cfg,
            chiuso=True,
            data_chiusura=datetime.now(),
            chiuso_da_utente_id=utente_id,
        )
        return ConfigurazioneBandaAnnoResponse.model_validate(updated)

    async def riapri_anno(self, cfg_id: int) -> ConfigurazioneBandaAnnoResponse:
        cfg = await self.repo.get_by_id(cfg_id)
        if not cfg:
            raise ConfigurazioneBandaAnnoNotFoundError(cfg_id)
        if not cfg.chiuso:
            raise AnnoGiaApertoError(cfg_id)
        updated = await self.repo.set_chiusura(
            cfg,
            chiuso=False,
            data_chiusura=None,
            chiuso_da_utente_id=None,
        )
        return ConfigurazioneBandaAnnoResponse.model_validate(updated)
