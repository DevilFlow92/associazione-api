from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.scheda_alunno import (
    SchedaAlunnoIscrizioneNotFoundError,
    SchedaAlunnoNotFoundError,
)
from app.exceptions.scheda_alunno_voce import (
    SchedaAlunnoVoceNotFoundError,
    VoceCatalogoNonCompatibileError,
)
from app.exceptions.voce_programma_catalogo import VoceProgrammaCatalogoNotFoundError
from app.models.corso import Corso
from app.models.scheda_alunno import SchedaAlunno
from app.models.scheda_alunno_voce import SchedaAlunnoVoce
from app.models.scheda_alunno_voce_storico import SchedaAlunnoVoceStorico
from app.models.utente import Utente
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.scheda_alunno_repository import SchedaAlunnoRepository
from app.repositories.scheda_alunno_voce_repository import SchedaAlunnoVoceRepository
from app.repositories.scheda_alunno_voce_storico_repository import (
    SchedaAlunnoVoceStoricoRepository,
)
from app.repositories.voce_programma_catalogo_repository import (
    VoceProgrammaCatalogoRepository,
)
from app.schemas.scheda_alunno import PersonaInSchedaAlunno
from app.schemas.scheda_alunno_voce import (
    SchedaAlunnoVoceCreate,
    SchedaAlunnoVoceResponse,
    SchedaAlunnoVoceUpdate,
)
from app.schemas.scheda_alunno_voce_storico import SchedaAlunnoVoceStoricoResponse
from app.services.rbac_row_level import (
    assert_puo_leggere_scheda,
    assert_puo_scrivere_scheda,
)


class SchedaAlunnoVoceService:
    """CRUD delle voci di programma di una scheda alunno, con la relativa
    scrittura sullo storico dei cambi di stato.

    Nessuna nuova regola di autorizzazione: le voci appartengono alla
    scheda, quindi vale esattamente ``assert_puo_scrivere_scheda`` risalendo
    scheda -> iscrizione_corso -> corso, lo stesso controllo già usato da
    ``SchedaAlunnoService``. La lettura delle voci non passa da qui: arriva
    incorporata nella ``SchedaAlunnoResponse`` (campo ``voci``).

    Creazione e cancellazione toccano sia la voce sia lo storico in
    un'unica transazione (``add_no_commit``/``flush``/``commit``, stesso
    pattern di ``IscrizioneService`` per l'auto-flusso di cassa): un crash a
    metà strada non deve mai lasciare una voce senza la sua riga di storico
    iniziale, né una voce cancellata con lo storico ancora agganciato.
    """

    def __init__(
        self,
        repo: SchedaAlunnoVoceRepository,
        scheda_repo: SchedaAlunnoRepository,
        iscrizione_corso_repo: IscrizioneCorsoRepository,
        catalogo_repo: VoceProgrammaCatalogoRepository,
        storico_repo: SchedaAlunnoVoceStoricoRepository,
    ) -> None:
        self.repo = repo
        self.scheda_repo = scheda_repo
        self.iscrizione_corso_repo = iscrizione_corso_repo
        self.catalogo_repo = catalogo_repo
        self.storico_repo = storico_repo

    async def _scheda_e_corso(
        self, scheda_alunno_id: int
    ) -> tuple[SchedaAlunno, Corso]:
        scheda = await self.scheda_repo.get_by_id(scheda_alunno_id)
        if not scheda:
            raise SchedaAlunnoNotFoundError(scheda_alunno_id)
        iscrizione = await self.iscrizione_corso_repo.get_by_id(
            scheda.iscrizione_corso_id
        )
        if not iscrizione:
            raise IscrizioneCorsoNotFoundError(scheda.iscrizione_corso_id)
        return scheda, iscrizione.corso

    async def _voce_di_scheda(
        self, scheda_alunno_id: int, voce_id: int
    ) -> SchedaAlunnoVoce:
        voce = await self.repo.get_by_id(voce_id)
        if not voce or voce.scheda_alunno_id != scheda_alunno_id:
            raise SchedaAlunnoVoceNotFoundError(voce_id)
        return voce

    async def create(
        self, scheda_alunno_id: int, data: SchedaAlunnoVoceCreate, utente: Utente
    ) -> SchedaAlunnoVoceResponse:
        scheda, corso = await self._scheda_e_corso(scheda_alunno_id)
        assert_puo_scrivere_scheda(utente, corso)

        voce_catalogo = await self.catalogo_repo.get_by_id(data.voce_catalogo_id)
        if not voce_catalogo:
            raise VoceProgrammaCatalogoNotFoundError(data.voce_catalogo_id)
        if (
            not voce_catalogo.attiva
            or voce_catalogo.tipo_corso_codice != corso.tipo_corso_codice
        ):
            raise VoceCatalogoNonCompatibileError(
                data.voce_catalogo_id, corso.tipo_corso_codice
            )

        voce = SchedaAlunnoVoce(scheda_alunno_id=scheda_alunno_id, **data.model_dump())
        self.repo.add_no_commit(voce)
        await self.repo.flush()  # assegna voce.id, serve alla riga di storico

        self.storico_repo.add_no_commit(
            SchedaAlunnoVoceStorico(
                scheda_alunno_voce_id=voce.id,
                scheda_alunno_id=scheda_alunno_id,
                voce_catalogo_id=data.voce_catalogo_id,
                stato_precedente=None,
                stato_nuovo=data.stato,
                modificato_da_persona_id=utente.persona_id,
            )
        )
        await self.repo.commit()
        self.scheda_repo.expire(scheda)

        result = await self.repo.get_by_id(voce.id)
        assert result is not None
        return SchedaAlunnoVoceResponse.model_validate(result)

    async def update(
        self,
        scheda_alunno_id: int,
        voce_id: int,
        data: SchedaAlunnoVoceUpdate,
        utente: Utente,
    ) -> SchedaAlunnoVoceResponse:
        scheda, corso = await self._scheda_e_corso(scheda_alunno_id)
        assert_puo_scrivere_scheda(utente, corso)
        voce = await self._voce_di_scheda(scheda_alunno_id, voce_id)

        stato_precedente = voce.stato
        self.repo.update_no_commit(voce, data)

        # Solo un cambio di stato è una transizione da tracciare: modifiche
        # a dettaglio/ordine senza cambio di stato non scrivono storico.
        if data.stato is not None and data.stato != stato_precedente:
            self.storico_repo.add_no_commit(
                SchedaAlunnoVoceStorico(
                    scheda_alunno_voce_id=voce.id,
                    scheda_alunno_id=scheda_alunno_id,
                    voce_catalogo_id=voce.voce_catalogo_id,
                    stato_precedente=stato_precedente,
                    stato_nuovo=data.stato,
                    modificato_da_persona_id=utente.persona_id,
                )
            )
        await self.repo.commit()
        self.scheda_repo.expire(scheda)

        result = await self.repo.get_by_id(voce_id)
        assert result is not None
        return SchedaAlunnoVoceResponse.model_validate(result)

    async def delete(self, scheda_alunno_id: int, voce_id: int, utente: Utente) -> None:
        scheda, corso = await self._scheda_e_corso(scheda_alunno_id)
        assert_puo_scrivere_scheda(utente, corso)
        voce = await self._voce_di_scheda(scheda_alunno_id, voce_id)

        await self.storico_repo.azzera_riferimento_no_commit(voce.id)
        await self.repo.delete_no_commit(voce)
        await self.repo.commit()
        self.scheda_repo.expire(scheda)

    # ── Storico dei cambi di stato (sola lettura, card #219) ─────────────────
    #
    # Superficie personale corsi: nessun controllo row-level qui, stessa
    # guardia dichiarativa ``corsi:read`` del resto del CRUD di questo
    # router (``get_by_id``/``get_all`` di ``SchedaAlunnoService`` non
    # applicano ``assert_puo_leggere_scheda`` neppure loro — vedi il
    # commento di modulo "CRUD del personale corsi"). ``assert_puo_leggere_scheda``
    # richiederebbe ``corsi:write`` o la proprietà della scheda, negando
    # l'accesso a un insegnante con il solo ``corsi:read`` — DEVIAZIONE dal
    # testo della card #219 (che chiedeva di riusarla anche qui) per
    # restare coerenti con il pattern del progetto e con il punto 10 della
    # card stessa ("200 con corsi:read, 403 senza").

    async def get_storico(
        self, scheda_alunno_id: int, params: PageParams
    ) -> PagedResponse[SchedaAlunnoVoceStoricoResponse]:
        scheda = await self.scheda_repo.get_by_id(scheda_alunno_id)
        if not scheda:
            raise SchedaAlunnoNotFoundError(scheda_alunno_id)
        return await self._storico_paginato(scheda_alunno_id, params)

    async def get_proprio_storico(
        self, iscrizione_corso_id: int, params: PageParams, utente: Utente
    ) -> PagedResponse[SchedaAlunnoVoceStoricoResponse]:
        iscrizione = await self.iscrizione_corso_repo.get_by_id(iscrizione_corso_id)
        if not iscrizione:
            raise IscrizioneCorsoNotFoundError(iscrizione_corso_id)
        assert_puo_leggere_scheda(utente, iscrizione.persona_id)
        scheda = await self.scheda_repo.get_by_iscrizione_corso_id(iscrizione_corso_id)
        if not scheda:
            raise SchedaAlunnoIscrizioneNotFoundError(iscrizione_corso_id)
        return await self._storico_paginato(scheda.id, params)

    async def _storico_paginato(
        self, scheda_alunno_id: int, params: PageParams
    ) -> PagedResponse[SchedaAlunnoVoceStoricoResponse]:
        righe = await self.storico_repo.get_by_scheda_alunno_id(
            scheda_alunno_id, offset=params.offset, limit=params.limit
        )
        total = await self.storico_repo.count_by_scheda_alunno_id(scheda_alunno_id)
        items = [
            SchedaAlunnoVoceStoricoResponse(
                id=riga.id,
                stato_precedente=riga.stato_precedente,
                stato_nuovo=riga.stato_nuovo,
                data_modifica=riga.data_modifica,
                modificato_da=(
                    PersonaInSchedaAlunno.model_validate(riga.modificato_da)
                    if riga.modificato_da is not None
                    else None
                ),
                voce_testo=voce_testo,
            )
            for riga, voce_testo in righe
        ]
        return paginate(items, total, params)
