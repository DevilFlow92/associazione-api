from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.corso import Corso
from app.schemas.corso import CorsoCreate, CorsoUpdate

_LOAD_OPTS = [
    selectinload(Corso.tipo_corso),
    selectinload(Corso.coordinatore),
    selectinload(Corso.insegnante),
]


class CorsoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        banda_codice: int | None = None,
        anno: int | None = None,
        tipo_corso_codice: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Corso]:
        stmt = select(Corso).options(*_LOAD_OPTS)
        if banda_codice is not None:
            stmt = stmt.where(Corso.banda_codice == banda_codice)
        if anno is not None:
            stmt = stmt.where(Corso.anno == anno)
        if tipo_corso_codice is not None:
            stmt = stmt.where(Corso.tipo_corso_codice == tipo_corso_codice)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        banda_codice: int | None = None,
        anno: int | None = None,
        tipo_corso_codice: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Corso)
        if banda_codice is not None:
            stmt = stmt.where(Corso.banda_codice == banda_codice)
        if anno is not None:
            stmt = stmt.where(Corso.anno == anno)
        if tipo_corso_codice is not None:
            stmt = stmt.where(Corso.tipo_corso_codice == tipo_corso_codice)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, corso_id: int) -> Corso | None:
        stmt = select(Corso).where(Corso.id == corso_id).options(*_LOAD_OPTS)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: CorsoCreate) -> Corso:
        corso = Corso(**data.model_dump())
        self.db.add(corso)
        await self.db.flush()
        corso_id = corso.id
        await self.db.commit()
        result = await self.get_by_id(corso_id)
        assert result is not None
        return result

    async def update(self, corso: Corso, data: CorsoUpdate) -> Corso:
        corso_id = corso.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(corso, field, value)
        await self.db.commit()
        self.db.expire(corso)
        result = await self.get_by_id(corso_id)
        assert result is not None
        return result

    async def delete(self, corso: Corso) -> None:
        await self.db.delete(corso)
        await self.db.commit()
