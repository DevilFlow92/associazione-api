from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheda_alunno_materiale import SchedaAlunnoMateriale


class SchedaAlunnoMaterialeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, materiale_id: int) -> SchedaAlunnoMateriale | None:
        stmt = select(SchedaAlunnoMateriale).where(
            SchedaAlunnoMateriale.id == materiale_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, materiale: SchedaAlunnoMateriale) -> SchedaAlunnoMateriale:
        self.db.add(materiale)
        await self.db.commit()
        await self.db.refresh(materiale)
        return materiale

    async def delete(self, materiale: SchedaAlunnoMateriale) -> None:
        await self.db.delete(materiale)
        await self.db.commit()
