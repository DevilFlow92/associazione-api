from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.spartito import Spartito
from app.schemas.spartito import SpartitoCreate, SpartitoUpdate


class SpartitoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        tipo_spartito_codice: int | None = None,
        strumento_codice: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Spartito]:
        stmt = select(Spartito)
        if tipo_spartito_codice is not None:
            stmt = stmt.where(Spartito.tipo_spartito_codice == tipo_spartito_codice)
        if strumento_codice is not None:
            stmt = stmt.where(Spartito.strumento_codice == strumento_codice)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        tipo_spartito_codice: int | None = None,
        strumento_codice: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Spartito)
        if tipo_spartito_codice is not None:
            stmt = stmt.where(Spartito.tipo_spartito_codice == tipo_spartito_codice)
        if strumento_codice is not None:
            stmt = stmt.where(Spartito.strumento_codice == strumento_codice)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, spartito_id: int) -> Spartito | None:
        stmt = select(Spartito).where(Spartito.id == spartito_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: SpartitoCreate) -> Spartito:
        spartito = Spartito(**data.model_dump())
        self.db.add(spartito)
        await self.db.commit()
        await self.db.refresh(spartito)
        return spartito

    async def update(self, spartito: Spartito, data: SpartitoUpdate) -> Spartito:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(spartito, field, value)
        await self.db.commit()
        await self.db.refresh(spartito)
        return spartito

    async def delete(self, spartito: Spartito) -> None:
        await self.db.delete(spartito)
        await self.db.commit()
