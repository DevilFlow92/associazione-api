from __future__ import annotations

from datetime import datetime, time

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.flusso_cassa import AnnoChiusoError
from app.exceptions.iscrizione import (
    ConfigurazioneContabileMancanteError,
    IscrizioneNotFoundError,
)
from app.exceptions.socio import SocioNotFoundError
from app.models.flusso_cassa import FlussoCassa, TipoFlussoCassa
from app.models.iscrizione import Iscrizione
from app.models.lookups import NaturaFlusso, StatoIscrizione
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.repositories.flusso_cassa_repository import FlussoCassaRepository
from app.repositories.iscrizione_repository import IscrizioneRepository
from app.repositories.lookup import LookupRepository
from app.repositories.socio_repository import SocioRepository
from app.schemas.iscrizione import (
    IscrizioneCreate,
    IscrizioneResponse,
    IscrizioneUpdate,
)


class IscrizioneService:
    def __init__(
        self,
        repo: IscrizioneRepository,
        socio_repo: SocioRepository,
        flusso_repo: FlussoCassaRepository,
        cfg_repo: ConfigurazioneBandaAnnoRepository,
        stato_iscrizione_repo: LookupRepository[StatoIscrizione],
        natura_flusso_repo: LookupRepository[NaturaFlusso],
    ) -> None:
        self.repo = repo
        self.socio_repo = socio_repo
        self.flusso_repo = flusso_repo
        self.cfg_repo = cfg_repo
        self.stato_iscrizione_repo = stato_iscrizione_repo
        self.natura_flusso_repo = natura_flusso_repo

    # ── Lookup helpers ────────────────────────────────────────────────────────

    async def _is_pagata(self, stato_iscrizione_codice: int) -> bool:
        stato = await self.stato_iscrizione_repo.get_by_descrizione_ilike("Pagata")
        return stato is not None and stato.codice == stato_iscrizione_codice

    async def _get_voce_quote(self, banda_codice: int, anno: int) -> int:
        cfg = await self.cfg_repo.get_by_banda_anno(banda_codice, anno)
        if cfg is None or cfg.voce_contabilita_quote_id is None:
            raise ConfigurazioneContabileMancanteError(banda_codice, anno)
        return cfg.voce_contabilita_quote_id

    async def _get_natura_banca(self) -> int:
        natura = await self.natura_flusso_repo.get_by_descrizione_ilike("Banca")
        if natura is None:
            raise ValueError("Natura flusso 'Banca' non trovata nel database")
        return natura.codice

    # ── Auto-flusso helpers ───────────────────────────────────────────────────

    async def _create_auto_flusso(self, iscrizione: Iscrizione) -> None:
        """Crea il FlussoCassa AUTO_ISCRIZIONE.
        Usa iscrizione.socio.persona (deve essere caricato)."""
        persona = iscrizione.socio.persona
        banda_codice = persona.banda_codice
        anno = iscrizione.anno
        if await self.cfg_repo.is_anno_chiuso(banda_codice, anno):
            raise AnnoChiusoError(banda_codice, anno)
        voce_id = await self._get_voce_quote(banda_codice, anno)
        natura_codice = await self._get_natura_banca()
        self.flusso_repo.add_no_commit(
            FlussoCassa(
                data_registrazione=datetime.combine(
                    iscrizione.data_iscrizione, time(0, 0)
                ),
                descrizione_operazione=(
                    f"Quota associativa {anno} - {persona.nome} {persona.cognome}"
                ),
                voce_contabilita_id=voce_id,
                importo=iscrizione.quota_partecipazione,
                segno="+",
                natura_flusso_codice=natura_codice,
                tipo=TipoFlussoCassa.AUTO_ISCRIZIONE,
                iscrizione_id=iscrizione.id,
            )
        )

    async def _delete_auto_flusso(self, iscrizione: Iscrizione) -> None:
        """Elimina il FlussoCassa AUTO_ISCRIZIONE legato all'iscrizione."""
        flusso = await self.flusso_repo.get_by_iscrizione_id(iscrizione.id)
        if flusso is None:
            return
        banda_codice = iscrizione.socio.persona.banda_codice
        anno = flusso.data_registrazione.year
        if await self.cfg_repo.is_anno_chiuso(banda_codice, anno):
            raise AnnoChiusoError(banda_codice, anno)
        await self.flusso_repo.delete_no_commit(flusso)

    async def _update_auto_flusso(self, iscrizione: Iscrizione, updates: dict) -> None:
        """Aggiorna importo e/o data_registrazione del FlussoCassa AUTO_ISCRIZIONE."""
        flusso = await self.flusso_repo.get_by_iscrizione_id(iscrizione.id)
        if flusso is None:
            return
        banda_codice = iscrizione.socio.persona.banda_codice
        current_anno = flusso.data_registrazione.year
        if await self.cfg_repo.is_anno_chiuso(banda_codice, current_anno):
            raise AnnoChiusoError(banda_codice, current_anno)
        new_data_reg = updates.get("data_registrazione")
        if new_data_reg is not None and new_data_reg.year != current_anno:
            if await self.cfg_repo.is_anno_chiuso(banda_codice, new_data_reg.year):
                raise AnnoChiusoError(banda_codice, new_data_reg.year)
        self.flusso_repo.update_no_commit(flusso, **updates)

    # ── CRUD ─────────────────────────────────────────────────────────────────

    async def get_all(
        self,
        socio_id: int | None,
        anno: int | None,
        params: PageParams,
    ) -> PagedResponse[IscrizioneResponse]:
        iscrizioni = await self.repo.get_all(
            socio_id=socio_id, anno=anno, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_all(socio_id=socio_id, anno=anno)
        items = [IscrizioneResponse.model_validate(i) for i in iscrizioni]
        return paginate(items, total, params)

    async def get_by_id(self, iscrizione_id: int) -> IscrizioneResponse:
        iscrizione = await self.repo.get_by_id(iscrizione_id)
        if not iscrizione:
            raise IscrizioneNotFoundError(iscrizione_id)
        return IscrizioneResponse.model_validate(iscrizione)

    async def create(self, data: IscrizioneCreate) -> IscrizioneResponse:
        socio = await self.socio_repo.get_by_id(data.socio_id)
        if not socio:
            raise SocioNotFoundError(data.socio_id)

        is_pagata = await self._is_pagata(data.stato_iscrizione_codice)

        # Validate before inserting so that a closed-anno or missing-config error
        # rolls back the entire operation (iscrizione never hits the DB).
        voce_id = None
        natura_codice = None
        if is_pagata:
            banda_codice = socio.persona.banda_codice
            if await self.cfg_repo.is_anno_chiuso(banda_codice, data.anno):
                raise AnnoChiusoError(banda_codice, data.anno)
            voce_id = await self._get_voce_quote(banda_codice, data.anno)
            natura_codice = await self._get_natura_banca()

        iscrizione = Iscrizione(**data.model_dump())
        self.repo.add_no_commit(iscrizione)

        if is_pagata:
            await self.repo.flush()  # assigns iscrizione.id
            persona = socio.persona
            self.flusso_repo.add_no_commit(
                FlussoCassa(
                    data_registrazione=datetime.combine(
                        data.data_iscrizione, time(0, 0)
                    ),
                    descrizione_operazione=(
                        f"Quota associativa {data.anno} - "
                        f"{persona.nome} {persona.cognome}"
                    ),
                    voce_contabilita_id=voce_id,
                    importo=data.quota_partecipazione,
                    segno="+",
                    natura_flusso_codice=natura_codice,
                    tipo=TipoFlussoCassa.AUTO_ISCRIZIONE,
                    iscrizione_id=iscrizione.id,
                )
            )

        await self.repo.commit()
        await self.repo.refresh(iscrizione)
        return IscrizioneResponse.model_validate(iscrizione)

    async def update(
        self, iscrizione_id: int, data: IscrizioneUpdate
    ) -> IscrizioneResponse:
        iscrizione = await self.repo.get_by_id(iscrizione_id)
        if not iscrizione:
            raise IscrizioneNotFoundError(iscrizione_id)

        old_stato = iscrizione.stato_iscrizione_codice
        old_pagata = await self._is_pagata(old_stato)
        new_stato_codice = (
            data.stato_iscrizione_codice
            if data.stato_iscrizione_codice is not None
            else old_stato
        )
        new_pagata = await self._is_pagata(new_stato_codice)

        # Apply all field changes to the in-memory iscrizione before side-effects
        # so helpers see the final values (e.g. updated quota/data_iscrizione).
        self.repo.update_no_commit(iscrizione, data)

        if not old_pagata and new_pagata:
            await self._create_auto_flusso(iscrizione)
        elif old_pagata and not new_pagata:
            await self._delete_auto_flusso(iscrizione)
        elif old_pagata and new_pagata:
            flusso_updates: dict = {}
            if data.quota_partecipazione is not None:
                flusso_updates["importo"] = iscrizione.quota_partecipazione
            if data.data_iscrizione is not None:
                flusso_updates["data_registrazione"] = datetime.combine(
                    iscrizione.data_iscrizione, time(0, 0)
                )
            if flusso_updates:
                await self._update_auto_flusso(iscrizione, flusso_updates)

        await self.repo.commit()
        await self.repo.refresh(iscrizione)
        return IscrizioneResponse.model_validate(iscrizione)

    async def delete(self, iscrizione_id: int) -> None:
        iscrizione = await self.repo.get_by_id(iscrizione_id)
        if not iscrizione:
            raise IscrizioneNotFoundError(iscrizione_id)

        if await self._is_pagata(iscrizione.stato_iscrizione_codice):
            banda_codice = iscrizione.socio.persona.banda_codice
            anno = iscrizione.anno
            if await self.cfg_repo.is_anno_chiuso(banda_codice, anno):
                raise AnnoChiusoError(banda_codice, anno)
            flusso = await self.flusso_repo.get_by_iscrizione_id(iscrizione_id)
            if flusso is not None:
                await self.flusso_repo.delete_no_commit(flusso)

        await self.repo.delete_no_commit(iscrizione)
        await self.repo.commit()
