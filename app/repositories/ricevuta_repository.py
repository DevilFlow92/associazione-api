from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.esterno import Esterno
from app.models.ricevuta import Ricevuta
from app.schemas.ricevuta import RicevutaCreate, RicevutaUpdate

_LOAD_OPTS = [
    selectinload(Ricevuta.esterno).selectinload(Esterno.persona),
]


class RicevutaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[Ricevuta]:
        stmt = select(Ricevuta).options(*_LOAD_OPTS).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(Ricevuta)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, ricevuta_id: int) -> Ricevuta | None:
        stmt = select(Ricevuta).where(Ricevuta.id == ricevuta_id).options(*_LOAD_OPTS)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_servizio(
        self, servizio_id: int, offset: int = 0, limit: int = 20
    ) -> list[Ricevuta]:
        stmt = (
            select(Ricevuta)
            .where(Ricevuta.servizio_id == servizio_id)
            .options(*_LOAD_OPTS)
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
        await self.db.flush()
        ricevuta_id = ricevuta.id
        await self.db.commit()
        result = await self.get_by_id(ricevuta_id)
        assert result is not None
        return result

    async def update(self, ricevuta: Ricevuta, data: RicevutaUpdate) -> Ricevuta:
        ricevuta_id = ricevuta.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(ricevuta, field, value)
        await self.db.commit()
        result = await self.get_by_id(ricevuta_id)
        assert result is not None
        return result

    async def delete(self, ricevuta: Ricevuta) -> None:
        await self.db.delete(ricevuta)
        await self.db.commit()
