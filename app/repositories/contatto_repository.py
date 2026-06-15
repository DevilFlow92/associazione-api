from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contatto import Contatto
from app.schemas.contatto import ContattoCreate, ContattoUpdate


class ContattoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[Contatto]:
        stmt = select(Contatto).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(Contatto)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, contatto_id: int) -> Contatto | None:
        stmt = select(Contatto).where(Contatto.id == contatto_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_persona(
        self, persona_id: int, offset: int = 0, limit: int = 20
    ) -> list[Contatto]:
        stmt = (
            select(Contatto)
            .where(Contatto.persona_id == persona_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_persona(self, persona_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Contatto)
            .where(Contatto.persona_id == persona_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, data: ContattoCreate) -> Contatto:
        contatto = Contatto(**data.model_dump())
        self.db.add(contatto)
        await self.db.commit()
        await self.db.refresh(contatto)
        return contatto

    async def update(self, contatto: Contatto, data: ContattoUpdate) -> Contatto:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(contatto, field, value)
        await self.db.commit()
        await self.db.refresh(contatto)
        return contatto

    async def delete(self, contatto: Contatto) -> None:
        await self.db.delete(contatto)
        await self.db.commit()
