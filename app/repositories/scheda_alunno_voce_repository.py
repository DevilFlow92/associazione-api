from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scheda_alunno_voce import SchedaAlunnoVoce
from app.models.voce_programma_catalogo import VoceProgrammaCatalogo
from app.schemas.scheda_alunno_voce import SchedaAlunnoVoceUpdate

_LOAD_OPTS = [
    selectinload(SchedaAlunnoVoce.voce_catalogo).selectinload(
        VoceProgrammaCatalogo.tipo_corso
    ),
    selectinload(SchedaAlunnoVoce.voce_catalogo).selectinload(
        VoceProgrammaCatalogo.categoria
    ),
]


class SchedaAlunnoVoceRepository:
    """Le operazioni di scrittura non fanno commit da sole (``*_no_commit``):
    creazione e cancellazione di una voce vanno sempre in transazione unica
    con la relativa riga di storico — vedi ``SchedaAlunnoVoceService`` e lo
    stesso pattern già in uso in ``IscrizioneRepository``/``IscrizioneService``
    per l'auto-flusso di cassa.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, voce_id: int) -> SchedaAlunnoVoce | None:
        stmt = (
            select(SchedaAlunnoVoce)
            .where(SchedaAlunnoVoce.id == voce_id)
            .options(*_LOAD_OPTS)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def add_no_commit(self, voce: SchedaAlunnoVoce) -> None:
        self.db.add(voce)

    def update_no_commit(
        self, voce: SchedaAlunnoVoce, data: SchedaAlunnoVoceUpdate
    ) -> None:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(voce, field, value)

    async def delete_no_commit(self, voce: SchedaAlunnoVoce) -> None:
        await self.db.delete(voce)

    async def flush(self) -> None:
        await self.db.flush()

    async def commit(self) -> None:
        await self.db.commit()
