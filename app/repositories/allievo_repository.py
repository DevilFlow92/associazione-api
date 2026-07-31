from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.allievo import Allievo
from app.models.persona import Persona
from app.schemas.allievo import AllievoCreate, AllievoUpdate

_LOAD_OPTS = [
    selectinload(Allievo.indirizzo),
    selectinload(Allievo.persona).selectinload(Persona.comune_nascita),
]


class AllievoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self, offset: int = 0, limit: int = 20, banda_codice: int | None = None
    ) -> list[Allievo]:
        stmt = select(Allievo).options(*_LOAD_OPTS)
        if banda_codice is not None:
            stmt = stmt.join(Persona).where(Persona.banda_codice == banda_codice)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, banda_codice: int | None = None) -> int:
        stmt = select(func.count()).select_from(Allievo)
        if banda_codice is not None:
            stmt = stmt.join(Persona).where(Persona.banda_codice == banda_codice)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, allievo_id: int) -> Allievo | None:
        stmt = select(Allievo).where(Allievo.id == allievo_id).options(*_LOAD_OPTS)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_codice(self, codice_allievo: str) -> Allievo | None:
        stmt = select(Allievo).where(Allievo.codice_allievo == codice_allievo)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_persona_id(self, persona_id: int) -> Allievo | None:
        stmt = select(Allievo).where(Allievo.persona_id == persona_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: AllievoCreate) -> Allievo:
        allievo = Allievo(**data.model_dump())
        self.db.add(allievo)
        await self.db.flush()
        allievo_id = allievo.id
        await self.db.commit()
        result = await self.get_by_id(allievo_id)
        assert result is not None
        return result

    async def update(self, allievo: Allievo, data: AllievoUpdate) -> Allievo:
        allievo_id = allievo.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(allievo, field, value)
        await self.db.commit()
        result = await self.get_by_id(allievo_id)
        assert result is not None
        return result

    async def delete(self, allievo: Allievo) -> None:
        await self.db.delete(allievo)
        await self.db.commit()
