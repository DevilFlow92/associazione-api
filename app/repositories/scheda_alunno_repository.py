from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scheda_alunno import SchedaAlunno
from app.schemas.scheda_alunno import SchedaAlunnoCreate, SchedaAlunnoUpdate

_LOAD_OPTS = [
    selectinload(SchedaAlunno.iscrizione_corso),
    selectinload(SchedaAlunno.aggiornato_da),
]


class SchedaAlunnoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        iscrizione_corso_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[SchedaAlunno]:
        stmt = select(SchedaAlunno).options(*_LOAD_OPTS)
        if iscrizione_corso_id is not None:
            stmt = stmt.where(SchedaAlunno.iscrizione_corso_id == iscrizione_corso_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, iscrizione_corso_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(SchedaAlunno)
        if iscrizione_corso_id is not None:
            stmt = stmt.where(SchedaAlunno.iscrizione_corso_id == iscrizione_corso_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, scheda_alunno_id: int) -> SchedaAlunno | None:
        stmt = (
            select(SchedaAlunno)
            .where(SchedaAlunno.id == scheda_alunno_id)
            .options(*_LOAD_OPTS)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_iscrizione_corso_id(
        self, iscrizione_corso_id: int
    ) -> SchedaAlunno | None:
        stmt = (
            select(SchedaAlunno)
            .where(SchedaAlunno.iscrizione_corso_id == iscrizione_corso_id)
            .options(*_LOAD_OPTS)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self, data: SchedaAlunnoCreate, aggiornato_da_persona_id: int | None
    ) -> SchedaAlunno:
        scheda = SchedaAlunno(
            **data.model_dump(), aggiornato_da_persona_id=aggiornato_da_persona_id
        )
        self.db.add(scheda)
        await self.db.flush()
        scheda_id = scheda.id
        await self.db.commit()
        result = await self.get_by_id(scheda_id)
        assert result is not None
        return result

    async def update(
        self,
        scheda: SchedaAlunno,
        data: SchedaAlunnoUpdate,
        aggiornato_da_persona_id: int | None,
    ) -> SchedaAlunno:
        scheda_id = scheda.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(scheda, field, value)
        scheda.aggiornato_da_persona_id = aggiornato_da_persona_id
        await self.db.commit()
        self.db.expire(scheda)
        result = await self.get_by_id(scheda_id)
        assert result is not None
        return result

    async def delete(self, scheda: SchedaAlunno) -> None:
        await self.db.delete(scheda)
        await self.db.commit()
