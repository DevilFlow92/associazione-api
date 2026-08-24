from __future__ import annotations

from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.scheda_alunno import SchedaAlunnoIscrizioneNotFoundError
from app.exceptions.scheda_alunno_autovalutazione import (
    SchedaAlunnoAutovalutazioneNotFoundError,
)
from app.models.iscrizione_corso import IscrizioneCorso
from app.models.scheda_alunno import SchedaAlunno
from app.models.scheda_alunno_autovalutazione import SchedaAlunnoAutovalutazione
from app.models.utente import Utente
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.scheda_alunno_autovalutazione_repository import (
    SchedaAlunnoAutovalutazioneRepository,
)
from app.repositories.scheda_alunno_repository import SchedaAlunnoRepository
from app.schemas.scheda_alunno_autovalutazione import (
    SchedaAlunnoAutovalutazioneCreate,
    SchedaAlunnoAutovalutazioneResponse,
    SchedaAlunnoAutovalutazioneUpdate,
)
from app.services.rbac_row_level import assert_puo_scrivere_autovalutazione


class SchedaAlunnoAutovalutazioneService:
    """CRUD del diario di autovalutazione dell'alunno sulla propria scheda.

    Perimetro row-level dedicato (``assert_puo_scrivere_autovalutazione``),
    NON quello di ``SchedaAlunnoService``/``SchedaAlunnoVoceService``: qui
    l'unico autorizzato a scrivere è l'alunno proprietario, mai il personale
    corsi — vedi il docstring della funzione in ``rbac_row_level`` per il
    perché.

    Gli endpoint sono indicizzati per ``iscrizione_corso_id`` (come
    ``SchedaAlunnoService.get_propria_scheda``), non per ``scheda_alunno_id``:
    l'alunno conosce la propria iscrizione, non l'id della scheda.
    """

    def __init__(
        self,
        repo: SchedaAlunnoAutovalutazioneRepository,
        scheda_repo: SchedaAlunnoRepository,
        iscrizione_corso_repo: IscrizioneCorsoRepository,
    ) -> None:
        self.repo = repo
        self.scheda_repo = scheda_repo
        self.iscrizione_corso_repo = iscrizione_corso_repo

    async def _iscrizione(self, iscrizione_corso_id: int) -> IscrizioneCorso:
        iscrizione = await self.iscrizione_corso_repo.get_by_id(iscrizione_corso_id)
        if not iscrizione:
            raise IscrizioneCorsoNotFoundError(iscrizione_corso_id)
        return iscrizione

    async def _scheda_autorizzata(
        self, iscrizione_corso_id: int, utente: Utente
    ) -> SchedaAlunno:
        """Risolve la scheda dell'iscrizione, autorizzazione prima di tutto:
        stesso ordine "authz prima di ricerca" già in uso da
        ``SchedaAlunnoService.get_propria_scheda`` — un alunno non
        proprietario non deve poter distinguere "scheda assente" da "scheda
        presente ma non tua" (in entrambi i casi 403, non 404)."""
        iscrizione = await self._iscrizione(iscrizione_corso_id)
        assert_puo_scrivere_autovalutazione(utente, iscrizione.persona_id)
        scheda = await self.scheda_repo.get_by_iscrizione_corso_id(iscrizione_corso_id)
        if not scheda:
            raise SchedaAlunnoIscrizioneNotFoundError(iscrizione_corso_id)
        return scheda

    async def _autovalutazione_di_scheda(
        self,
        scheda_alunno_id: int,
        autovalutazione_id: int,
        persona_id: int | None,
    ) -> SchedaAlunnoAutovalutazione:
        """Verifica che la voce appartenga alla scheda indicata E sia stata
        scritta da questa stessa persona: ridondante con l'unicità di
        alunno-per-scheda già garantita dal row-level, ma esplicito e a
        prova di refactor futuro (se mai più alunni condividessero una
        scheda, questo controllo resta corretto)."""
        autovalutazione = await self.repo.get_by_id(autovalutazione_id)
        if (
            not autovalutazione
            or autovalutazione.scheda_alunno_id != scheda_alunno_id
            or autovalutazione.persona_id != persona_id
        ):
            raise SchedaAlunnoAutovalutazioneNotFoundError(autovalutazione_id)
        return autovalutazione

    async def create(
        self,
        iscrizione_corso_id: int,
        data: SchedaAlunnoAutovalutazioneCreate,
        utente: Utente,
    ) -> SchedaAlunnoAutovalutazioneResponse:
        scheda = await self._scheda_autorizzata(iscrizione_corso_id, utente)
        autovalutazione = SchedaAlunnoAutovalutazione(
            scheda_alunno_id=scheda.id,
            persona_id=utente.persona_id,
            testo=data.testo,
        )
        created = await self.repo.create(autovalutazione)
        self.scheda_repo.expire(scheda)
        return SchedaAlunnoAutovalutazioneResponse.model_validate(created)

    async def update(
        self,
        iscrizione_corso_id: int,
        autovalutazione_id: int,
        data: SchedaAlunnoAutovalutazioneUpdate,
        utente: Utente,
    ) -> SchedaAlunnoAutovalutazioneResponse:
        scheda = await self._scheda_autorizzata(iscrizione_corso_id, utente)
        autovalutazione = await self._autovalutazione_di_scheda(
            scheda.id, autovalutazione_id, utente.persona_id
        )
        updated = await self.repo.update(autovalutazione, data)
        self.scheda_repo.expire(scheda)
        return SchedaAlunnoAutovalutazioneResponse.model_validate(updated)

    async def delete(
        self, iscrizione_corso_id: int, autovalutazione_id: int, utente: Utente
    ) -> None:
        scheda = await self._scheda_autorizzata(iscrizione_corso_id, utente)
        autovalutazione = await self._autovalutazione_di_scheda(
            scheda.id, autovalutazione_id, utente.persona_id
        )
        await self.repo.delete(autovalutazione)
        self.scheda_repo.expire(scheda)
