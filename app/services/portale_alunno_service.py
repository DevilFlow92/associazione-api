from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.models.iscrizione_corso import IscrizioneCorso
from app.models.utente import Utente
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.lezione_repository import LezioneRepository
from app.repositories.pagamento_corso_repository import PagamentoCorsoRepository
from app.repositories.presenza_repository import PresenzaRepository
from app.schemas.iscrizione_corso import IscrizioneCorsoResponse
from app.schemas.lezione import LezioneResponse
from app.schemas.pagamento_corso import PagamentoCorsoResponse
from app.schemas.presenza import PresenzaResponse
from app.services.rbac_row_level import (
    assert_e_titolare_iscrizione,
    assert_ha_persona_collegata,
)


class PortaleAlunnoService:
    """Le viste self-service dell'alunno sulle proprie iscrizioni corso.

    Ogni vista scoped a un'iscrizione ripete lo stesso schema: carica
    l'iscrizione (404 se assente), verifica la proprietà (403 se non è
    dell'utente, stesso ordine "esistenza poi authz" già in uso da
    ``SchedaAlunnoService.get_propria_scheda``), poi interroga la risorsa
    figlia filtrando per ``corso_id``/``persona_id`` dell'iscrizione — mai
    per ``iscrizione_corso_id`` direttamente, perché Lezione e Presenza non
    lo conoscono (vedi ``PresenzaRepository.get_by_corso_e_persona``).
    """

    def __init__(
        self,
        iscrizione_corso_repo: IscrizioneCorsoRepository,
        lezione_repo: LezioneRepository,
        presenza_repo: PresenzaRepository,
        pagamento_corso_repo: PagamentoCorsoRepository,
    ) -> None:
        self.iscrizione_corso_repo = iscrizione_corso_repo
        self.lezione_repo = lezione_repo
        self.presenza_repo = presenza_repo
        self.pagamento_corso_repo = pagamento_corso_repo

    async def _iscrizione_di_titolarita(
        self, iscrizione_corso_id: int, utente: Utente
    ) -> IscrizioneCorso:
        iscrizione = await self.iscrizione_corso_repo.get_by_id(iscrizione_corso_id)
        if not iscrizione:
            raise IscrizioneCorsoNotFoundError(iscrizione_corso_id)
        assert_e_titolare_iscrizione(utente, iscrizione.persona_id)
        return iscrizione

    async def get_mie_iscrizioni(
        self, params: PageParams, utente: Utente
    ) -> PagedResponse[IscrizioneCorsoResponse]:
        """Punto di ingresso del portale: le iscrizioni della propria Persona."""
        assert_ha_persona_collegata(utente)
        iscrizioni = await self.iscrizione_corso_repo.get_all(
            persona_id=utente.persona_id, offset=params.offset, limit=params.limit
        )
        total = await self.iscrizione_corso_repo.count_all(persona_id=utente.persona_id)
        items = [IscrizioneCorsoResponse.model_validate(i) for i in iscrizioni]
        return paginate(items, total, params)

    async def get_mio_calendario(
        self, iscrizione_corso_id: int, params: PageParams, utente: Utente
    ) -> PagedResponse[LezioneResponse]:
        iscrizione = await self._iscrizione_di_titolarita(iscrizione_corso_id, utente)
        lezioni = await self.lezione_repo.get_all(
            corso_id=iscrizione.corso_id, offset=params.offset, limit=params.limit
        )
        total = await self.lezione_repo.count_all(corso_id=iscrizione.corso_id)
        items = [LezioneResponse.model_validate(le) for le in lezioni]
        return paginate(items, total, params)

    async def get_mie_presenze(
        self, iscrizione_corso_id: int, params: PageParams, utente: Utente
    ) -> PagedResponse[PresenzaResponse]:
        iscrizione = await self._iscrizione_di_titolarita(iscrizione_corso_id, utente)
        presenze = await self.presenza_repo.get_by_corso_e_persona(
            iscrizione.corso_id,
            iscrizione.persona_id,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.presenza_repo.count_by_corso_e_persona(
            iscrizione.corso_id, iscrizione.persona_id
        )
        items = [PresenzaResponse.model_validate(p) for p in presenze]
        return paginate(items, total, params)

    async def get_miei_pagamenti(
        self, iscrizione_corso_id: int, params: PageParams, utente: Utente
    ) -> PagedResponse[PagamentoCorsoResponse]:
        iscrizione = await self._iscrizione_di_titolarita(iscrizione_corso_id, utente)
        pagamenti = await self.pagamento_corso_repo.get_all(
            iscrizione_corso_id=iscrizione.id,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.pagamento_corso_repo.count_all(
            iscrizione_corso_id=iscrizione.id
        )
        items = [PagamentoCorsoResponse.model_validate(p) for p in pagamenti]
        return paginate(items, total, params)
