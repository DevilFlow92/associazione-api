from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheda_alunno_voce_storico import SchedaAlunnoVoceStorico


class SchedaAlunnoVoceStoricoRepository:
    """Scrittura soltanto: append-only, nessuna lettura in questa card — la
    superficie di consultazione dello storico è la card #219.

    Nessun metodo commit-immediato: ogni scrittura entra nella stessa
    transazione della voce a cui si riferisce, chiusa da
    ``SchedaAlunnoVoceRepository.commit()`` — vedi ``SchedaAlunnoVoceService``.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def add_no_commit(self, riga: SchedaAlunnoVoceStorico) -> None:
        self.db.add(riga)

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
