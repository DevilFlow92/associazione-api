from __future__ import annotations

from datetime import datetime

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.flusso_cassa import AnnoChiusoError, FlussoCassaNotFoundError
from app.exceptions.voce_contabilita import VoceContabilitaNotFoundError
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.repositories.flusso_cassa_repository import FlussoCassaRepository
from app.repositories.voce_contabilita_repository import VoceContabilitaRepository
from app.schemas.flusso_cassa import (
    FlussoCassaCreate,
    FlussoCassaResponse,
    FlussoCassaUpdate,
)


class FlussoCassaService:
    def __init__(
        self,
        repo: FlussoCassaRepository,
        voce_repo: VoceContabilitaRepository,
        cfg_repo: ConfigurazioneBandaAnnoRepository,
    ) -> None:
        self.repo = repo
        self.voce_repo = voce_repo
        self.cfg_repo = cfg_repo

    async def _assert_anno_aperto(
        self, voce_contabilita_id: int, data_registrazione: datetime
    ) -> None:
        voce = await self.voce_repo.get_by_id(voce_contabilita_id)
        if voce is None:
            return
        anno = data_registrazione.year
        if await self.cfg_repo.is_anno_chiuso(voce.banda_codice, anno):
            raise AnnoChiusoError(voce.banda_codice, anno)

    async def get_all(self, params: PageParams) -> PagedResponse[FlussoCassaResponse]:
        flussi = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [FlussoCassaResponse.model_validate(f) for f in flussi]
        return paginate(items, total, params)

    async def get_by_voce(
        self, voce_contabilita_id: int, params: PageParams
    ) -> PagedResponse[FlussoCassaResponse]:
        voce = await self.voce_repo.get_by_id(voce_contabilita_id)
        if not voce:
            raise VoceContabilitaNotFoundError(voce_contabilita_id)
        flussi = await self.repo.get_by_voce(
            voce_contabilita_id, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_by_voce(voce_contabilita_id)
        items = [FlussoCassaResponse.model_validate(f) for f in flussi]
        return paginate(items, total, params)

    async def get_by_id(self, flusso_id: int) -> FlussoCassaResponse:
        flusso = await self.repo.get_by_id(flusso_id)
        if not flusso:
            raise FlussoCassaNotFoundError(flusso_id)
        return FlussoCassaResponse.model_validate(flusso)

    async def create(self, data: FlussoCassaCreate) -> FlussoCassaResponse:
        await self._assert_anno_aperto(
            data.voce_contabilita_id, data.data_registrazione
        )
        voce = await self.voce_repo.get_by_id(data.voce_contabilita_id)
        if not voce:
            raise VoceContabilitaNotFoundError(data.voce_contabilita_id)
        flusso = await self.repo.create(data)
        return FlussoCassaResponse.model_validate(flusso)

    async def update(
        self, flusso_id: int, data: FlussoCassaUpdate
    ) -> FlussoCassaResponse:
        flusso = await self.repo.get_by_id(flusso_id)
        if not flusso:
            raise FlussoCassaNotFoundError(flusso_id)

        await self._assert_anno_aperto(
            flusso.voce_contabilita_id, flusso.data_registrazione
        )

        # If data_registrazione is being changed to a different year, also
        # check the target (banda, new_year).
        new_data_reg = data.data_registrazione
        if (
            new_data_reg is not None
            and new_data_reg.year != flusso.data_registrazione.year
        ):
            await self._assert_anno_aperto(flusso.voce_contabilita_id, new_data_reg)

        updated = await self.repo.update(flusso, data)
        return FlussoCassaResponse.model_validate(updated)

    async def delete(self, flusso_id: int) -> None:
        flusso = await self.repo.get_by_id(flusso_id)
        if not flusso:
            raise FlussoCassaNotFoundError(flusso_id)
        await self._assert_anno_aperto(
            flusso.voce_contabilita_id, flusso.data_registrazione
        )
        await self.repo.delete(flusso)
