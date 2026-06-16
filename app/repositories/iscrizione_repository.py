from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iscrizione import Iscrizione
from app.schemas.iscrizione import IscrizioneCreate, IscrizioneUpdate


class IscrizioneRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        socio_id: int | None = None,
        anno: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Iscrizione]:
        stmt = select(Iscrizione)
        if socio_id is not None:
            stmt = stmt.where(Iscrizione.socio_id == socio_id)
        if anno is not None:
            stmt = stmt.where(Iscrizione.anno == anno)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        socio_id: int | None = None,
        anno: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Iscrizione)
        if socio_id is not None:
            stmt = stmt.where(Iscrizione.socio_id == socio_id)
        if anno is not None:
            stmt = stmt.where(Iscrizione.anno == anno)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, iscrizione_id: int) -> Iscrizione | None:
        stmt = select(Iscrizione).where(Iscrizione.id == iscrizione_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: IscrizioneCreate) -> Iscrizione:
        iscrizione = Iscrizione(**data.model_dump())
        self.db.add(iscrizione)
        await self.db.commit()
        await self.db.refresh(iscrizione)
        return iscrizione

    async def update(
        self, iscrizione: Iscrizione, data: IscrizioneUpdate
    ) -> Iscrizione:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(iscrizione, field, value)
        await self.db.commit()
        await self.db.refresh(iscrizione)
        return iscrizione

    async def delete(self, iscrizione: Iscrizione) -> None:
        await self.db.delete(iscrizione)
        await self.db.commit()
