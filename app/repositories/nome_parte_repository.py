from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.nome_parte import NomeParte
from app.schemas.spartito import NomeParteCreate, NomeParteUpdate

_LOAD_OPTS = [
    selectinload(NomeParte.tipo_spartito),
    selectinload(NomeParte.documento_audio),
    selectinload(NomeParte.spartiti),
]


class NomeParteRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        banda_codice: int,
        tipo_spartito_codice: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[NomeParte]:
        stmt = (
            select(NomeParte)
            .options(*_LOAD_OPTS)
            .where(NomeParte.banda_codice == banda_codice)
        )
        if tipo_spartito_codice is not None:
            stmt = stmt.where(NomeParte.tipo_spartito_codice == tipo_spartito_codice)
        stmt = stmt.order_by(NomeParte.nome).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        banda_codice: int,
        tipo_spartito_codice: int | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(NomeParte)
            .where(NomeParte.banda_codice == banda_codice)
        )
        if tipo_spartito_codice is not None:
            stmt = stmt.where(NomeParte.tipo_spartito_codice == tipo_spartito_codice)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, id: int) -> NomeParte | None:
        stmt = select(NomeParte).where(NomeParte.id == id).options(*_LOAD_OPTS)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: NomeParteCreate) -> NomeParte:
        obj = NomeParte(**data.model_dump())
        self.db.add(obj)
        await self.db.flush()
        obj_id = obj.id
        await self.db.commit()
        result = await self.get_by_id(obj_id)
        assert result is not None
        return result

    async def update(self, obj: NomeParte, data: NomeParteUpdate) -> NomeParte:
        obj_id = obj.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        await self.db.commit()
        # Expire the object so that selectinload in get_by_id issues fresh
        # subqueries — necessary when the session is long-lived (e.g. tests)
        # and relationship attributes were already populated before this update.
        self.db.expire(obj)
        result = await self.get_by_id(obj_id)
        assert result is not None
        return result

    async def delete(self, obj: NomeParte) -> None:
        await self.db.delete(obj)
        await self.db.commit()
