from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.esterno import Esterno
from app.schemas.esterno import EsternoCreate, EsternoUpdate

_LOAD_OPTS = [selectinload(Esterno.strumento), selectinload(Esterno.persona)]


class EsternoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self, offset: int = 0, limit: int = 20, banda_codice: int | None = None
    ) -> list[Esterno]:
        stmt = select(Esterno).options(*_LOAD_OPTS)
        if banda_codice is not None:
            stmt = stmt.where(Esterno.banda_codice == banda_codice)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, banda_codice: int | None = None) -> int:
        stmt = select(func.count()).select_from(Esterno)
        if banda_codice is not None:
            stmt = stmt.where(Esterno.banda_codice == banda_codice)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, esterno_id: int) -> Esterno | None:
        stmt = select(Esterno).where(Esterno.id == esterno_id).options(*_LOAD_OPTS)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_codice(self, codice_esterno: str) -> Esterno | None:
        stmt = select(Esterno).where(Esterno.codice_esterno == codice_esterno)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: EsternoCreate) -> Esterno:
        esterno = Esterno(**data.model_dump())
        self.db.add(esterno)
        await self.db.flush()
        esterno_id = esterno.id
        await self.db.commit()
        result = await self.get_by_id(esterno_id)
        assert result is not None
        return result

    async def update(self, esterno: Esterno, data: EsternoUpdate) -> Esterno:
        esterno_id = esterno.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(esterno, field, value)
        await self.db.commit()
        result = await self.get_by_id(esterno_id)
        assert result is not None
        return result

    async def delete(self, esterno: Esterno) -> None:
        await self.db.delete(esterno)
        await self.db.commit()
