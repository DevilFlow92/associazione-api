from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.iscrizione_corso import IscrizioneCorso
from app.schemas.iscrizione_corso import IscrizioneCorsoCreate, IscrizioneCorsoUpdate

_LOAD_OPTS = [
    selectinload(IscrizioneCorso.corso),
    selectinload(IscrizioneCorso.persona),
    selectinload(IscrizioneCorso.stato_iscrizione_corso),
    selectinload(IscrizioneCorso.documento),
]


class IscrizioneCorsoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        corso_id: int | None = None,
        persona_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[IscrizioneCorso]:
        stmt = select(IscrizioneCorso).options(*_LOAD_OPTS)
        if corso_id is not None:
            stmt = stmt.where(IscrizioneCorso.corso_id == corso_id)
        if persona_id is not None:
            stmt = stmt.where(IscrizioneCorso.persona_id == persona_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        corso_id: int | None = None,
        persona_id: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(IscrizioneCorso)
        if corso_id is not None:
            stmt = stmt.where(IscrizioneCorso.corso_id == corso_id)
        if persona_id is not None:
            stmt = stmt.where(IscrizioneCorso.persona_id == persona_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, iscrizione_corso_id: int) -> IscrizioneCorso | None:
        stmt = (
            select(IscrizioneCorso)
            .where(IscrizioneCorso.id == iscrizione_corso_id)
            .options(*_LOAD_OPTS)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: IscrizioneCorsoCreate) -> IscrizioneCorso:
        iscrizione_corso = IscrizioneCorso(**data.model_dump())
        self.db.add(iscrizione_corso)
        await self.db.flush()
        iscrizione_corso_id = iscrizione_corso.id
        await self.db.commit()
        result = await self.get_by_id(iscrizione_corso_id)
        assert result is not None
        return result

    async def update(
        self, iscrizione_corso: IscrizioneCorso, data: IscrizioneCorsoUpdate
    ) -> IscrizioneCorso:
        iscrizione_corso_id = iscrizione_corso.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(iscrizione_corso, field, value)
        await self.db.commit()
        self.db.expire(iscrizione_corso)
        result = await self.get_by_id(iscrizione_corso_id)
        assert result is not None
        return result

    async def delete(self, iscrizione_corso: IscrizioneCorso) -> None:
        await self.db.delete(iscrizione_corso)
        await self.db.commit()
