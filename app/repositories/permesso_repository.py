from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permesso import Permesso


class PermessoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[Permesso]:
        stmt = select(Permesso).order_by(Permesso.codice).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(Permesso)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_codici(self, codici: list[str]) -> list[Permesso]:
        if not codici:
            return []
        stmt = select(Permesso).where(Permesso.codice.in_(codici))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
