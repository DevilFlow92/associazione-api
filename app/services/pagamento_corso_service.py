from __future__ import annotations

from datetime import datetime, time

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.flusso_cassa import AnnoChiusoError
from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.pagamento_corso import (
    ConfigurazioneContabileCorsiMancanteError,
    PagamentoCorsoNotFoundError,
)
from app.models.flusso_cassa import FlussoCassa, TipoFlussoCassa
from app.models.iscrizione_corso import IscrizioneCorso
from app.models.lookups import NaturaFlusso
from app.models.pagamento_corso import PagamentoCorso
from app.models.persona import Persona
from app.models.ricevuta import Ricevuta, TipoRicevuta
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.repositories.flusso_cassa_repository import FlussoCassaRepository
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.lookup import LookupRepository
from app.repositories.pagamento_corso_repository import PagamentoCorsoRepository
from app.repositories.ricevuta_repository import RicevutaRepository
from app.schemas.pagamento_corso import (
    PagamentoCorsoCreate,
    PagamentoCorsoResponse,
    PagamentoCorsoUpdate,
)


class PagamentoCorsoService:
    def __init__(
        self,
        repo: PagamentoCorsoRepository,
        iscrizione_corso_repo: IscrizioneCorsoRepository,
        ricevuta_repo: RicevutaRepository,
        flusso_repo: FlussoCassaRepository,
        cfg_repo: ConfigurazioneBandaAnnoRepository,
        natura_flusso_repo: LookupRepository[NaturaFlusso],
    ) -> None:
        self.repo = repo
        self.iscrizione_corso_repo = iscrizione_corso_repo
        self.ricevuta_repo = ricevuta_repo
        self.flusso_repo = flusso_repo
        self.cfg_repo = cfg_repo
        self.natura_flusso_repo = natura_flusso_repo

    # ── Helpers contabili ─────────────────────────────────────────────────────

    async def _get_voce_corsi(self, banda_codice: int, anno: int) -> int:
        cfg = await self.cfg_repo.get_by_banda_anno(banda_codice, anno)
        if cfg is None or cfg.voce_contabilita_corsi_id is None:
            raise ConfigurazioneContabileCorsiMancanteError(banda_codice, anno)
        return cfg.voce_contabilita_corsi_id

    async def _get_natura_banca(self) -> int:
        natura = await self.natura_flusso_repo.get_by_descrizione_ilike("Banca")
        if natura is None:
            raise ValueError("Natura flusso 'Banca' non trovata nel database")
        return natura.codice

    @staticmethod
    def _descrizione_operazione(
        iscrizione_corso: IscrizioneCorso, persona: Persona
    ) -> str:
        return (
            f"Retta corso {iscrizione_corso.corso_id} "
            f"({iscrizione_corso.corso.anno}) - {persona.nome} {persona.cognome}"
        )

    async def _get_iscrizione_corso_or_raise(
        self, iscrizione_corso_id: int
    ) -> IscrizioneCorso:
        iscrizione_corso = await self.iscrizione_corso_repo.get_by_id(
            iscrizione_corso_id
        )
        if not iscrizione_corso:
            raise IscrizioneCorsoNotFoundError(iscrizione_corso_id)
        return iscrizione_corso

    # ── CRUD ─────────────────────────────────────────────────────────────────

    async def get_all(
        self, iscrizione_corso_id: int | None, params: PageParams
    ) -> PagedResponse[PagamentoCorsoResponse]:
        pagamenti = await self.repo.get_all(
            iscrizione_corso_id=iscrizione_corso_id,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(iscrizione_corso_id=iscrizione_corso_id)
        items = [PagamentoCorsoResponse.model_validate(p) for p in pagamenti]
        return paginate(items, total, params)

    async def get_by_id(self, pagamento_corso_id: int) -> PagamentoCorsoResponse:
        pagamento = await self.repo.get_by_id(pagamento_corso_id)
        if not pagamento:
            raise PagamentoCorsoNotFoundError(pagamento_corso_id)
        return PagamentoCorsoResponse.model_validate(pagamento)

    async def create(self, data: PagamentoCorsoCreate) -> PagamentoCorsoResponse:
        iscrizione_corso = await self._get_iscrizione_corso_or_raise(
            data.iscrizione_corso_id
        )
        corso = iscrizione_corso.corso
        persona = iscrizione_corso.persona
        banda_codice = corso.banda_codice
        anno = corso.anno

        # Validazioni prima di scrivere qualunque riga: un errore di
        # configurazione mancante o anno chiuso non deve lasciare tracce
        # parziali (stesso principio di IscrizioneService.create).
        if await self.cfg_repo.is_anno_chiuso(banda_codice, anno):
            raise AnnoChiusoError(banda_codice, anno)
        voce_id = await self._get_voce_corsi(banda_codice, anno)
        natura_codice = await self._get_natura_banca()

        data_ricevuta = datetime.combine(data.data_pagamento, time(0, 0))

        ricevuta = Ricevuta(
            data_ricevuta=data_ricevuta,
            importo=data.importo,
            tipo_ricevuta=TipoRicevuta.RISCOSSIONE,
            persona_id=persona.id,
        )
        self.ricevuta_repo.add_no_commit(ricevuta)
        await self.repo.flush()  # assegna ricevuta.id

        pagamento = PagamentoCorso(
            iscrizione_corso_id=data.iscrizione_corso_id,
            data_pagamento=data.data_pagamento,
            importo=data.importo,
            ricevuta_id=ricevuta.id,
            note=data.note,
        )
        self.repo.add_no_commit(pagamento)
        await self.repo.flush()  # assegna pagamento.id

        self.flusso_repo.add_no_commit(
            FlussoCassa(
                data_registrazione=data_ricevuta,
                descrizione_operazione=self._descrizione_operazione(
                    iscrizione_corso, persona
                ),
                voce_contabilita_id=voce_id,
                importo=data.importo,
                segno="+",
                natura_flusso_codice=natura_codice,
                tipo=TipoFlussoCassa.AUTO_PAGAMENTO_CORSO,
                pagamento_corso_id=pagamento.id,
            )
        )

        await self.repo.commit()
        await self.repo.refresh(pagamento)
        return PagamentoCorsoResponse.model_validate(pagamento)

    async def update(
        self, pagamento_corso_id: int, data: PagamentoCorsoUpdate
    ) -> PagamentoCorsoResponse:
        pagamento = await self.repo.get_by_id(pagamento_corso_id)
        if not pagamento:
            raise PagamentoCorsoNotFoundError(pagamento_corso_id)

        iscrizione_corso = await self._get_iscrizione_corso_or_raise(
            pagamento.iscrizione_corso_id
        )
        banda_codice = iscrizione_corso.corso.banda_codice
        anno = iscrizione_corso.corso.anno
        if await self.cfg_repo.is_anno_chiuso(banda_codice, anno):
            raise AnnoChiusoError(banda_codice, anno)

        self.repo.update_no_commit(pagamento, data)

        flusso_updates: dict = {}
        ricevuta_updates: dict = {}
        if data.importo is not None:
            flusso_updates["importo"] = data.importo
            ricevuta_updates["importo"] = data.importo
        if data.data_pagamento is not None:
            nuova_data = datetime.combine(data.data_pagamento, time(0, 0))
            flusso_updates["data_registrazione"] = nuova_data
            ricevuta_updates["data_ricevuta"] = nuova_data

        if flusso_updates:
            flusso = await self.flusso_repo.get_by_pagamento_corso_id(
                pagamento_corso_id
            )
            if flusso is not None:
                self.flusso_repo.update_no_commit(flusso, **flusso_updates)
        if ricevuta_updates and pagamento.ricevuta is not None:
            self.ricevuta_repo.update_no_commit(pagamento.ricevuta, **ricevuta_updates)

        await self.repo.commit()
        await self.repo.refresh(pagamento)
        return PagamentoCorsoResponse.model_validate(pagamento)

    async def delete(self, pagamento_corso_id: int) -> None:
        pagamento = await self.repo.get_by_id(pagamento_corso_id)
        if not pagamento:
            raise PagamentoCorsoNotFoundError(pagamento_corso_id)

        iscrizione_corso = await self._get_iscrizione_corso_or_raise(
            pagamento.iscrizione_corso_id
        )
        banda_codice = iscrizione_corso.corso.banda_codice
        anno = iscrizione_corso.corso.anno
        if await self.cfg_repo.is_anno_chiuso(banda_codice, anno):
            raise AnnoChiusoError(banda_codice, anno)

        # Cascata: FlussoCassa e Ricevuta sono generati automaticamente da
        # questo pagamento (nessun proprietario esterno), quindi vengono
        # rimossi insieme ad esso — non restano orfani.
        flusso = await self.flusso_repo.get_by_pagamento_corso_id(pagamento_corso_id)
        if flusso is not None:
            await self.flusso_repo.delete_no_commit(flusso)

        ricevuta = pagamento.ricevuta
        await self.repo.delete_no_commit(pagamento)
        if ricevuta is not None:
            await self.ricevuta_repo.delete_no_commit(ricevuta)

        await self.repo.commit()
