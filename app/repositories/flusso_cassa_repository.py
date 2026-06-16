from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flusso_cassa import FlussoCassa
from app.schemas.flusso_cassa import FlussoCassaCreate, FlussoCassaUpdate


class FlussoCassaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[FlussoCassa]:
        stmt = select(FlussoCassa).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(FlussoCassa)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, flusso_id: int) -> FlussoCassa | None:
        stmt = select(FlussoCassa).where(FlussoCassa.id == flusso_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_voce(
        self, voce_contabilita_id: int, offset: int = 0, limit: int = 20
    ) -> list[FlussoCassa]:
        stmt = (
            select(FlussoCassa)
            .where(FlussoCassa.voce_contabilita_id == voce_contabilita_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_voce(self, voce_contabilita_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(FlussoCassa)
            .where(FlussoCassa.voce_contabilita_id == voce_contabilita_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, data: FlussoCassaCreate) -> FlussoCassa:
        flusso = FlussoCassa(**data.model_dump())
        self.db.add(flusso)
        await self.db.commit()
        await self.db.refresh(flusso)
        return flusso

    async def update(self, flusso: FlussoCassa, data: FlussoCassaUpdate) -> FlussoCassa:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(flusso, field, value)
        await self.db.commit()
        await self.db.refresh(flusso)
        return flusso

    async def delete(self, flusso: FlussoCassa) -> None:
        await self.db.delete(flusso)
        await self.db.commit()
