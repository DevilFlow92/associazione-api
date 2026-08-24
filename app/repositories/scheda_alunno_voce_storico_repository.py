from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scheda_alunno_voce_storico import SchedaAlunnoVoceStorico
from app.models.voce_programma_catalogo import VoceProgrammaCatalogo


class SchedaAlunnoVoceStoricoRepository:
    """Scrittura append-only (card #214) più lettura paginata (card #219).

    Nessun metodo commit-immediato per la scrittura: ogni riga entra nella
    stessa transazione della voce a cui si riferisce, chiusa da
    ``SchedaAlunnoVoceRepository.commit()`` — vedi ``SchedaAlunnoVoceService``.

    La lettura arricchisce ogni riga con il testo della voce di catalogo
    tramite una query separata (non ``selectinload``): ``voce_catalogo_id``
    è denormalizzato di proposito (vedi il model), quindi non è una vera FK
    e la voce a cui si riferisce può non esistere più.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def add_no_commit(self, riga: SchedaAlunnoVoceStorico) -> None:
        self.db.add(riga)

    async def get_by_scheda_alunno_id(
        self, scheda_alunno_id: int, offset: int = 0, limit: int = 20
    ) -> list[tuple[SchedaAlunnoVoceStorico, str | None]]:
        """Righe di storico della scheda, più recenti prima, con il testo
        della voce di catalogo quando questa esiste ancora (``None`` se è
        stata cancellata — vedi il commento di classe).

        Ordinamento secondario per ``id`` decrescente: ``data_modifica`` ha
        risoluzione al secondo (``server_default=func.now()``), insufficiente
        a distinguere più transizioni scritte nello stesso secondo — l'id,
        assegnato in ordine di inserimento, è il tiebreaker deterministico.
        """
        stmt = (
            select(SchedaAlunnoVoceStorico)
            .where(SchedaAlunnoVoceStorico.scheda_alunno_id == scheda_alunno_id)
            .options(selectinload(SchedaAlunnoVoceStorico.modificato_da))
            .order_by(
                SchedaAlunnoVoceStorico.data_modifica.desc(),
                SchedaAlunnoVoceStorico.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        righe = list(result.scalars().all())

        voce_catalogo_ids = {riga.voce_catalogo_id for riga in righe}
        testi_by_id: dict[int, str] = {}
        if voce_catalogo_ids:
            stmt_testi = select(
                VoceProgrammaCatalogo.id, VoceProgrammaCatalogo.testo
            ).where(VoceProgrammaCatalogo.id.in_(voce_catalogo_ids))
            result_testi = await self.db.execute(stmt_testi)
            testi_by_id = {id_: testo for id_, testo in result_testi.all()}

        return [(riga, testi_by_id.get(riga.voce_catalogo_id)) for riga in righe]

    async def count_by_scheda_alunno_id(self, scheda_alunno_id: int) -> int:
        stmt = select(func.count()).where(
            SchedaAlunnoVoceStorico.scheda_alunno_id == scheda_alunno_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def azzera_riferimento_no_commit(self, scheda_alunno_voce_id: int) -> None:
        """Applicato a livello applicativo invece di affidarsi solo al FK
        ``ON DELETE SET NULL``: SQLite (usato nei test) non applica i vincoli
        di integrità referenziale senza ``PRAGMA foreign_keys``, quindi il
        comportamento va garantito qui per restare identico tra test e
        produzione (dove PostgreSQL applicherebbe comunque il vincolo)."""
        await self.db.execute(
            update(SchedaAlunnoVoceStorico)
            .where(
                SchedaAlunnoVoceStorico.scheda_alunno_voce_id == scheda_alunno_voce_id
            )
            .values(scheda_alunno_voce_id=None)
        )
