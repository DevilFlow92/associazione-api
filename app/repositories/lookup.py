from __future__ import annotations

from typing import Any

from pydantic import BaseModel as PydanticModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lookups import LookupBase


class LookupRepository[ModelT: LookupBase]:
    """Data access generico per le tabelle dimensione (lookup).

    Tutte le tabelle ``D_*`` condividono una chiave primaria ``codice`` e una
    ``descrizione``, quindi possono riusare lo stesso accesso ai dati.
    """

    def __init__(self, db: AsyncSession, model: type[ModelT]) -> None:
        self.db = db
        self.model = model

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelT]:
        stmt = select(self.model).order_by(self.model.codice)
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, filters: dict[str, Any] | None = None) -> int:
        stmt = select(func.count()).select_from(self.model)
        stmt = self._apply_filters(stmt, filters)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    def _apply_filters(self, stmt, filters: dict[str, Any] | None):
        for field, value in (filters or {}).items():
            stmt = stmt.where(getattr(self.model, field) == value)
        return stmt

    async def get_by_codice(self, codice: int) -> ModelT | None:
        stmt = select(self.model).where(self.model.codice == codice)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: PydanticModel) -> ModelT:
        obj = self.model(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: ModelT, data: PydanticModel) -> ModelT:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.db.delete(obj)
        await self.db.commit()
