from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheda_alunno_autovalutazione import SchedaAlunnoAutovalutazione
from app.schemas.scheda_alunno_autovalutazione import (
    SchedaAlunnoAutovalutazioneUpdate,
)


class SchedaAlunnoAutovalutazioneRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self, autovalutazione_id: int
    ) -> SchedaAlunnoAutovalutazione | None:
        stmt = select(SchedaAlunnoAutovalutazione).where(
            SchedaAlunnoAutovalutazione.id == autovalutazione_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self, autovalutazione: SchedaAlunnoAutovalutazione
    ) -> SchedaAlunnoAutovalutazione:
        self.db.add(autovalutazione)
        await self.db.commit()
        await self.db.refresh(autovalutazione)
        return autovalutazione

    async def update(
        self,
        autovalutazione: SchedaAlunnoAutovalutazione,
        data: SchedaAlunnoAutovalutazioneUpdate,
    ) -> SchedaAlunnoAutovalutazione:
        autovalutazione.testo = data.testo
        autovalutazione.data_modifica = datetime.now()
        await self.db.commit()
        await self.db.refresh(autovalutazione)
        return autovalutazione

    async def delete(self, autovalutazione: SchedaAlunnoAutovalutazione) -> None:
        await self.db.delete(autovalutazione)
        await self.db.commit()
