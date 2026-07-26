from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.nome_parte import NomeParte
from app.models.repertorio_item import RepertorioItem
from app.models.spartito import Spartito
from app.schemas.repertorio_item import RepertorioItemCreate, RepertorioItemUpdate

_LOAD_OPTS = [selectinload(RepertorioItem.nome_parte)]


class RepertorioItemRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, repertorio_item_id: int) -> RepertorioItem | None:
        stmt = (
            select(RepertorioItem)
            .where(RepertorioItem.id == repertorio_item_id)
            .options(*_LOAD_OPTS)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_servizio(
        self, servizio_id: int, offset: int = 0, limit: int = 20
    ) -> list[RepertorioItem]:
        stmt = (
            select(RepertorioItem)
            .where(RepertorioItem.servizio_id == servizio_id)
            .options(*_LOAD_OPTS)
            .order_by(RepertorioItem.ordine)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_servizio(self, servizio_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(RepertorioItem)
            .where(RepertorioItem.servizio_id == servizio_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_servizio_con_spartiti(
        self, servizio_id: int
    ) -> list[RepertorioItem]:
        """Repertorio del servizio, ordinato, con nome_parte.spartiti (e il
        documento di ciascuno spartito) caricati per il libretto PDF."""
        stmt = (
            select(RepertorioItem)
            .where(RepertorioItem.servizio_id == servizio_id)
            .options(
                selectinload(RepertorioItem.nome_parte)
                .selectinload(NomeParte.spartiti)
                .selectinload(Spartito.documento)
            )
            .order_by(RepertorioItem.ordine)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_prova(
        self, prova_id: int, offset: int = 0, limit: int = 20
    ) -> list[RepertorioItem]:
        stmt = (
            select(RepertorioItem)
            .where(RepertorioItem.prova_id == prova_id)
            .options(*_LOAD_OPTS)
            .order_by(RepertorioItem.ordine)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_prova(self, prova_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(RepertorioItem)
            .where(RepertorioItem.prova_id == prova_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_prova_con_spartiti(self, prova_id: int) -> list[RepertorioItem]:
        """Analogo a ``get_by_servizio_con_spartiti``, per il repertorio di una
        prova."""
        stmt = (
            select(RepertorioItem)
            .where(RepertorioItem.prova_id == prova_id)
            .options(
                selectinload(RepertorioItem.nome_parte)
                .selectinload(NomeParte.spartiti)
                .selectinload(Spartito.documento)
            )
            .order_by(RepertorioItem.ordine)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: RepertorioItemCreate) -> RepertorioItem:
        item = RepertorioItem(**data.model_dump())
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update(
        self, item: RepertorioItem, data: RepertorioItemUpdate
    ) -> RepertorioItem:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete(self, item: RepertorioItem) -> None:
        await self.db.delete(item)
        await self.db.commit()
