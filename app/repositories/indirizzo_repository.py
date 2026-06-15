from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.indirizzo import Indirizzo
from app.schemas.indirizzo import IndirizzoCreate, IndirizzoUpdate


class IndirizzoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[Indirizzo]:
        stmt = select(Indirizzo).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(Indirizzo)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, indirizzo_id: int) -> Indirizzo | None:
        stmt = select(Indirizzo).where(Indirizzo.id == indirizzo_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: IndirizzoCreate) -> Indirizzo:
        indirizzo = Indirizzo(**data.model_dump())
        self.db.add(indirizzo)
        await self.db.commit()
        await self.db.refresh(indirizzo)
        return indirizzo

    async def update(self, indirizzo: Indirizzo, data: IndirizzoUpdate) -> Indirizzo:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(indirizzo, field, value)
        await self.db.commit()
        await self.db.refresh(indirizzo)
        return indirizzo

    async def delete(self, indirizzo: Indirizzo) -> None:
        await self.db.delete(indirizzo)
        await self.db.commit()
