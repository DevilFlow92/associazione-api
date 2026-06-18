from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ricevuta import Ricevuta
from app.models.servizio import Servizio
from app.schemas.servizio import ServizioCreate, ServizioUpdate


class ServizioRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        anno: int | None = None,
        banda_codice: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Servizio]:
        stmt = select(Servizio)
        if anno is not None:
            stmt = stmt.where(Servizio.anno == anno)
        if banda_codice is not None:
            stmt = stmt.where(Servizio.banda_codice == banda_codice)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self, anno: int | None = None, banda_codice: int | None = None
    ) -> int:
        stmt = select(func.count()).select_from(Servizio)
        if anno is not None:
            stmt = stmt.where(Servizio.anno == anno)
        if banda_codice is not None:
            stmt = stmt.where(Servizio.banda_codice == banda_codice)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, servizio_id: int) -> Servizio | None:
        stmt = select(Servizio).where(Servizio.id == servizio_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_ricevute(self, servizio_id: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(Ricevuta)
            .where(Ricevuta.servizio_id == servizio_id)
        )
        return bool((await self.db.execute(stmt)).scalar_one())

    async def create(self, data: ServizioCreate) -> Servizio:
        servizio = Servizio(**data.model_dump())
        self.db.add(servizio)
        await self.db.commit()
        await self.db.refresh(servizio)
        return servizio

    async def update(self, servizio: Servizio, data: ServizioUpdate) -> Servizio:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(servizio, field, value)
        await self.db.commit()
        await self.db.refresh(servizio)
        return servizio

    async def delete(self, servizio: Servizio) -> None:
        await self.db.delete(servizio)
        await self.db.commit()
