from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ricevuta import Ricevuta
from app.schemas.ricevuta import RicevutaCreate, RicevutaUpdate


class RicevutaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[Ricevuta]:
        stmt = select(Ricevuta).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(Ricevuta)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, ricevuta_id: int) -> Ricevuta | None:
        stmt = select(Ricevuta).where(Ricevuta.id == ricevuta_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_servizio(
        self, servizio_id: int, offset: int = 0, limit: int = 20
    ) -> list[Ricevuta]:
        stmt = (
            select(Ricevuta)
            .where(Ricevuta.servizio_id == servizio_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_servizio(self, servizio_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Ricevuta)
            .where(Ricevuta.servizio_id == servizio_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, data: RicevutaCreate) -> Ricevuta:
        ricevuta = Ricevuta(**data.model_dump())
        self.db.add(ricevuta)
        await self.db.commit()
        await self.db.refresh(ricevuta)
        return ricevuta

    async def update(self, ricevuta: Ricevuta, data: RicevutaUpdate) -> Ricevuta:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(ricevuta, field, value)
        await self.db.commit()
        await self.db.refresh(ricevuta)
        return ricevuta

    async def delete(self, ricevuta: Ricevuta) -> None:
        await self.db.delete(ricevuta)
        await self.db.commit()
