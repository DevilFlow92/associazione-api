from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.indirizzo import Indirizzo
from app.models.lezione import Lezione
from app.models.lookups import Comune
from app.schemas.lezione import LezioneCreate, LezioneUpdate

_LOAD_OPTS = [
    selectinload(Lezione.corso),
    selectinload(Lezione.indirizzo)
    .selectinload(Indirizzo.comune)
    .selectinload(Comune.provincia),
]


class LezioneRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        corso_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Lezione]:
        stmt = select(Lezione).options(*_LOAD_OPTS)
        if corso_id is not None:
            stmt = stmt.where(Lezione.corso_id == corso_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, corso_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Lezione)
        if corso_id is not None:
            stmt = stmt.where(Lezione.corso_id == corso_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, lezione_id: int) -> Lezione | None:
        stmt = select(Lezione).where(Lezione.id == lezione_id).options(*_LOAD_OPTS)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: LezioneCreate) -> Lezione:
        lezione = Lezione(**data.model_dump())
        self.db.add(lezione)
        await self.db.flush()
        lezione_id = lezione.id
        await self.db.commit()
        result = await self.get_by_id(lezione_id)
        assert result is not None
        return result

    async def update(self, lezione: Lezione, data: LezioneUpdate) -> Lezione:
        lezione_id = lezione.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(lezione, field, value)
        await self.db.commit()
        self.db.expire(lezione)
        result = await self.get_by_id(lezione_id)
        assert result is not None
        return result

    async def delete(self, lezione: Lezione) -> None:
        await self.db.delete(lezione)
        await self.db.commit()
