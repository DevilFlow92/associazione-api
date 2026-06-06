from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iscrizione import Iscrizione
from app.schemas.iscrizione import IscrizioneCreate, IscrizioneUpdate


class IscrizioneRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_socio(self, socio_id: int) -> list[Iscrizione]:
        stmt = select(Iscrizione).where(Iscrizione.socio_id == socio_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, iscrizione_id: int) -> Iscrizione | None:
        stmt = select(Iscrizione).where(Iscrizione.id == iscrizione_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_socio_anno(self, socio_id: int, anno: int) -> Iscrizione | None:
        stmt = select(Iscrizione).where(
            Iscrizione.socio_id == socio_id, Iscrizione.anno == anno
        )
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
