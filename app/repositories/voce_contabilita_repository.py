from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flusso_cassa import FlussoCassa
from app.models.voce_contabilita import VoceContabilita
from app.schemas.voce_contabilita import (
    VoceContabilitaCreate,
    VoceContabilitaUpdate,
)


class VoceContabilitaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        banda_codice: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[VoceContabilita]:
        stmt = select(VoceContabilita)
        if banda_codice is not None:
            stmt = stmt.where(VoceContabilita.banda_codice == banda_codice)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, banda_codice: int | None = None) -> int:
        stmt = select(func.count()).select_from(VoceContabilita)
        if banda_codice is not None:
            stmt = stmt.where(VoceContabilita.banda_codice == banda_codice)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, voce_id: int) -> VoceContabilita | None:
        stmt = select(VoceContabilita).where(VoceContabilita.id == voce_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_flussi(self, voce_id: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(FlussoCassa)
            .where(FlussoCassa.voce_contabilita_id == voce_id)
        )
        return bool((await self.db.execute(stmt)).scalar_one())

    async def create(self, data: VoceContabilitaCreate) -> VoceContabilita:
        voce = VoceContabilita(**data.model_dump())
        self.db.add(voce)
        await self.db.commit()
        await self.db.refresh(voce)
        return voce

    async def update(
        self, voce: VoceContabilita, data: VoceContabilitaUpdate
    ) -> VoceContabilita:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(voce, field, value)
        await self.db.commit()
        await self.db.refresh(voce)
        return voce

    async def delete(self, voce: VoceContabilita) -> None:
        await self.db.delete(voce)
        await self.db.commit()
