from __future__ import annotations

from collections import Counter

from app.exceptions.persona import PersonaNotFoundError
from app.models.iscrizione_corso import IscrizioneCorso
from app.models.scheda_alunno import SchedaAlunno
from app.models.scheda_alunno_voce import StatoVoceProgramma
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.persona_repository import PersonaRepository
from app.repositories.scheda_alunno_repository import SchedaAlunnoRepository
from app.schemas.iscrizione_corso import CorsoInIscrizioneCorso
from app.schemas.percorso_formativo import (
    RiepilogoVociPercorsoFormativo,
    TappaPercorsoFormativo,
)


class PercorsoFormativoService:
    """Percorso formativo pluriennale di una persona (card #220): le sue
    schede alunno attraverso tutte le iscrizioni a corsi nel tempo, con un
    riepilogo delle voci per ciascuna.

    Superficie di sola lettura, aggregata su iscrizioni_corso + schede_alunno
    — entrambe risorse del dominio corsi, non anagrafiche pure. Nessun
    controllo row-level: è una superficie di gestione (insegnante/staff),
    non self-service alunno.
    """

    def __init__(
        self,
        persona_repo: PersonaRepository,
        iscrizione_corso_repo: IscrizioneCorsoRepository,
        scheda_repo: SchedaAlunnoRepository,
    ) -> None:
        self.persona_repo = persona_repo
        self.iscrizione_corso_repo = iscrizione_corso_repo
        self.scheda_repo = scheda_repo

    async def get_percorso_formativo(
        self, persona_id: int
    ) -> list[TappaPercorsoFormativo]:
        persona = await self.persona_repo.get_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(persona_id)

        iscrizioni = (
            await self.iscrizione_corso_repo.get_all_by_persona_ordinate_per_anno(
                persona_id
            )
        )
        schede = await self.scheda_repo.get_by_iscrizione_corso_ids(
            [iscrizione.id for iscrizione in iscrizioni]
        )
        schede_per_iscrizione = {s.iscrizione_corso_id: s for s in schede}

        return [
            self._tappa(iscrizione, schede_per_iscrizione.get(iscrizione.id))
            for iscrizione in iscrizioni
        ]

    def _tappa(
        self, iscrizione: IscrizioneCorso, scheda: SchedaAlunno | None
    ) -> TappaPercorsoFormativo:
        conteggi = Counter(voce.stato for voce in scheda.voci) if scheda else Counter()
        riepilogo = RiepilogoVociPercorsoFormativo(
            totale=sum(conteggi.values()),
            da_iniziare=conteggi[StatoVoceProgramma.DA_INIZIARE],
            in_corso=conteggi[StatoVoceProgramma.IN_CORSO],
            acquisita=conteggi[StatoVoceProgramma.ACQUISITA],
        )
        return TappaPercorsoFormativo(
            iscrizione_corso_id=iscrizione.id,
            corso=CorsoInIscrizioneCorso.model_validate(iscrizione.corso),
            scheda_alunno_id=scheda.id if scheda else None,
            riepilogo_voci=riepilogo,
        )
