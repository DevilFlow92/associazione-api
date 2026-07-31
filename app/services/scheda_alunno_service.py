from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.scheda_alunno import (
    SchedaAlunnoDuplicataError,
    SchedaAlunnoIscrizioneNotFoundError,
    SchedaAlunnoNotFoundError,
)
from app.models.iscrizione_corso import IscrizioneCorso
from app.models.utente import Utente
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.scheda_alunno_repository import SchedaAlunnoRepository
from app.schemas.scheda_alunno import (
    SchedaAlunnoCreate,
    SchedaAlunnoResponse,
    SchedaAlunnoUpdate,
)
from app.services.rbac_row_level import (
    assert_puo_leggere_scheda,
    assert_puo_scrivere_scheda,
)


class SchedaAlunnoService:
    """CRUD della scheda alunno più l'accesso row-level dell'alunno stesso.

    I metodi di scrittura ricevono il principal autenticato per due motivi:
    valorizzare l'audit ``aggiornato_da_persona_id`` e applicare il controllo
    row-level per-corso (``assert_puo_scrivere_scheda``). Qui il servizio non
    è ridondante rispetto alla guardia ``corsi:write`` del router: il router
    verifica solo il permesso, non se l'utente sia insegnante/coordinatore
    del corso specifico — quella verifica esiste solo qui, in un punto solo,
    così resta valida anche per chiamanti futuri che non passino dal router
    (portale alunno).
    """

    def __init__(
        self,
        repo: SchedaAlunnoRepository,
        iscrizione_corso_repo: IscrizioneCorsoRepository,
    ) -> None:
        self.repo = repo
        self.iscrizione_corso_repo = iscrizione_corso_repo

    async def _iscrizione(self, iscrizione_corso_id: int) -> IscrizioneCorso:
        """Risale dall'iscrizione all'alunno e al corso: sono il soggetto e
        il perimetro del controllo (``iscrizione.corso`` è eager-loaded da
        ``IscrizioneCorsoRepository``, nessuna query aggiuntiva)."""
        iscrizione = await self.iscrizione_corso_repo.get_by_id(iscrizione_corso_id)
        if not iscrizione:
            raise IscrizioneCorsoNotFoundError(iscrizione_corso_id)
        return iscrizione

    # ── Accesso del personale corsi (guardia RBAC nei router) ────────────────

    async def get_all(
        self, params: PageParams, iscrizione_corso_id: int | None = None
    ) -> PagedResponse[SchedaAlunnoResponse]:
        schede = await self.repo.get_all(
            iscrizione_corso_id=iscrizione_corso_id,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(iscrizione_corso_id=iscrizione_corso_id)
        items = [SchedaAlunnoResponse.model_validate(s) for s in schede]
        return paginate(items, total, params)

    async def get_by_id(self, scheda_alunno_id: int) -> SchedaAlunnoResponse:
        scheda = await self.repo.get_by_id(scheda_alunno_id)
        if not scheda:
            raise SchedaAlunnoNotFoundError(scheda_alunno_id)
        return SchedaAlunnoResponse.model_validate(scheda)

    async def create(
        self, data: SchedaAlunnoCreate, utente: Utente
    ) -> SchedaAlunnoResponse:
        iscrizione = await self._iscrizione(data.iscrizione_corso_id)
        assert_puo_scrivere_scheda(utente, iscrizione.corso)
        esistente = await self.repo.get_by_iscrizione_corso_id(data.iscrizione_corso_id)
        if esistente:
            raise SchedaAlunnoDuplicataError(data.iscrizione_corso_id)
        scheda = await self.repo.create(data, utente.persona_id)
        return SchedaAlunnoResponse.model_validate(scheda)

    async def update(
        self, scheda_alunno_id: int, data: SchedaAlunnoUpdate, utente: Utente
    ) -> SchedaAlunnoResponse:
        scheda = await self.repo.get_by_id(scheda_alunno_id)
        if not scheda:
            raise SchedaAlunnoNotFoundError(scheda_alunno_id)
        iscrizione = await self._iscrizione(scheda.iscrizione_corso_id)
        assert_puo_scrivere_scheda(utente, iscrizione.corso)
        updated = await self.repo.update(scheda, data, utente.persona_id)
        return SchedaAlunnoResponse.model_validate(updated)

    async def delete(self, scheda_alunno_id: int, utente: Utente) -> None:
        scheda = await self.repo.get_by_id(scheda_alunno_id)
        if not scheda:
            raise SchedaAlunnoNotFoundError(scheda_alunno_id)
        iscrizione = await self._iscrizione(scheda.iscrizione_corso_id)
        assert_puo_scrivere_scheda(utente, iscrizione.corso)
        await self.repo.delete(scheda)

    # ── Accesso row-level dell'alunno alla propria scheda ────────────────────

    async def get_propria_scheda(
        self, iscrizione_corso_id: int, utente: Utente
    ) -> SchedaAlunnoResponse:
        """Legge la scheda dell'iscrizione, se il principal ne ha titolo.

        L'ordine dei controlli è deliberato: esistenza dell'iscrizione (404),
        poi autorizzazione (403), poi esistenza della scheda (404). Valutare
        l'autorizzazione prima di cercare la scheda evita che un utente non
        autorizzato distingua "scheda assente" da "scheda presente ma non
        tua": in entrambi i casi riceve 403.
        """
        iscrizione = await self._iscrizione(iscrizione_corso_id)
        assert_puo_leggere_scheda(utente, iscrizione.persona_id)
        scheda = await self.repo.get_by_iscrizione_corso_id(iscrizione_corso_id)
        if not scheda:
            raise SchedaAlunnoIscrizioneNotFoundError(iscrizione_corso_id)
        return SchedaAlunnoResponse.model_validate(scheda)
