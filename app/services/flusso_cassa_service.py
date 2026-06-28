from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.flusso_cassa import (
    AnnoChiusoError,
    FlussoCassaNotFoundError,
    FlussoTrasferimentoNonModificabileError,
    NaturaFlussoNotFoundError,
    TrasferimentoNaturaUgualeError,
)
from app.exceptions.voce_contabilita import VoceContabilitaNotFoundError
from app.models.flusso_cassa import FlussoCassa, TipoFlussoCassa
from app.models.lookups import NaturaFlusso
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.repositories.flusso_cassa_repository import FlussoCassaRepository
from app.repositories.lookup import LookupRepository
from app.repositories.voce_contabilita_repository import VoceContabilitaRepository
from app.schemas.flusso_cassa import (
    FlussoCassaCreate,
    FlussoCassaResponse,
    FlussoCassaUpdate,
    TrasferimentoCreate,
)


class FlussoCassaService:
    def __init__(
        self,
        repo: FlussoCassaRepository,
        voce_repo: VoceContabilitaRepository,
        cfg_repo: ConfigurazioneBandaAnnoRepository,
        natura_repo: LookupRepository[NaturaFlusso],
    ) -> None:
        self.repo = repo
        self.voce_repo = voce_repo
        self.cfg_repo = cfg_repo
        self.natura_repo = natura_repo

    async def _assert_anno_aperto(
        self, voce_contabilita_id: int, data_registrazione: datetime
    ) -> None:
        voce = await self.voce_repo.get_by_id(voce_contabilita_id)
        if voce is None:
            return
        anno = data_registrazione.year
        if await self.cfg_repo.is_anno_chiuso(voce.banda_codice, anno):
            raise AnnoChiusoError(voce.banda_codice, anno)

    async def get_all(
        self, params: PageParams, anno: int | None = None
    ) -> PagedResponse[FlussoCassaResponse]:
        flussi = await self.repo.get_all(
            offset=params.offset, limit=params.limit, anno=anno
        )
        total = await self.repo.count_all(anno=anno)
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

    async def crea_trasferimento(self, data: TrasferimentoCreate) -> list[FlussoCassa]:
        """Crea atomicamente le due gambe (uscita + entrata) di un trasferimento.

        Le righe condividono lo stesso ``trasferimento_id`` e vengono inserite
        in un'unica transazione: se un insert fallisce, entrambi annullano.
        """
        if data.natura_da_codice == data.natura_a_codice:
            raise TrasferimentoNaturaUgualeError(data.natura_da_codice)

        for codice in (data.natura_da_codice, data.natura_a_codice):
            if await self.natura_repo.get_by_codice(codice) is None:
                raise NaturaFlussoNotFoundError(codice)

        voce = await self.voce_repo.get_by_id(data.voce_contabilita_id)
        if voce is None:
            raise VoceContabilitaNotFoundError(data.voce_contabilita_id)

        await self._assert_anno_aperto(
            data.voce_contabilita_id, data.data_registrazione
        )

        trasferimento_id = uuid4()
        shared = {
            "data_registrazione": data.data_registrazione,
            "descrizione_operazione": data.descrizione_operazione,
            "note": data.note,
            "voce_contabilita_id": data.voce_contabilita_id,
            "importo": data.importo,
            "trasferimento_id": trasferimento_id,
        }
        uscita = FlussoCassa(
            **shared,
            segno="-",
            natura_flusso_codice=data.natura_da_codice,
            tipo=TipoFlussoCassa.TRASFERIMENTO_USCITA,
        )
        entrata = FlussoCassa(
            **shared,
            segno="+",
            natura_flusso_codice=data.natura_a_codice,
            tipo=TipoFlussoCassa.TRASFERIMENTO_ENTRATA,
        )

        self.repo.add_no_commit(uscita)
        self.repo.add_no_commit(entrata)
        await self.repo.commit()
        await self.repo.refresh(uscita)
        await self.repo.refresh(entrata)
        return [uscita, entrata]

    async def update(
        self, flusso_id: int, data: FlussoCassaUpdate
    ) -> FlussoCassaResponse:
        flusso = await self.repo.get_by_id(flusso_id)
        if not flusso:
            raise FlussoCassaNotFoundError(flusso_id)

        if flusso.trasferimento_id is not None:
            raise FlussoTrasferimentoNonModificabileError(flusso_id)

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

        # Se è una gamba di un trasferimento, elimina anche l'altra: le due
        # righe sono indivisibili e vengono cancellate nella stessa transazione.
        other = None
        if flusso.trasferimento_id is not None:
            other = await self.repo.get_other_leg_by_trasferimento_id(
                flusso.trasferimento_id, flusso.id
            )
            if other is not None:
                await self._assert_anno_aperto(
                    other.voce_contabilita_id, other.data_registrazione
                )

        await self.repo.delete_no_commit(flusso)
        if other is not None:
            await self.repo.delete_no_commit(other)
        await self.repo.commit()
