from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.committente import Committente
from app.models.indirizzo import Indirizzo
from app.models.lookups import Comune
from app.models.servizio import Servizio
from app.schemas.committente import CommittenteCreate, CommittenteUpdate

_LOAD_OPTS = [
    selectinload(Committente.indirizzo)
    .selectinload(Indirizzo.comune)
    .selectinload(Comune.provincia),
]


class CommittenteRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[Committente]:
        stmt = select(Committente).options(*_LOAD_OPTS).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(Committente)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, committente_id: int) -> Committente | None:
        stmt = (
            select(Committente)
            .where(Committente.id == committente_id)
            .options(*_LOAD_OPTS)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_servizi(self, committente_id: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(Servizio)
            .where(Servizio.committente_id == committente_id)
        )
        return bool((await self.db.execute(stmt)).scalar_one())

    async def create(self, data: CommittenteCreate) -> Committente:
        committente = Committente(**data.model_dump())
        self.db.add(committente)
        await self.db.flush()
        committente_id = committente.id
        await self.db.commit()
        result = await self.get_by_id(committente_id)
        assert result is not None
        return result

    async def update(
        self, committente: Committente, data: CommittenteUpdate
    ) -> Committente:
        committente_id = committente.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(committente, field, value)
        await self.db.commit()
        result = await self.get_by_id(committente_id)
        assert result is not None
        return result

    async def delete(self, committente: Committente) -> None:
        await self.db.delete(committente)
        await self.db.commit()
