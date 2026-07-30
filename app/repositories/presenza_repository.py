from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.persona import Persona
from app.models.presenza import Presenza
from app.schemas.presenza import PresenzaCreate, PresenzaUpdate

_LOAD_OPTS = [selectinload(Presenza.persona)]


class PresenzaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, presenza_id: int) -> Presenza | None:
        stmt = select(Presenza).where(Presenza.id == presenza_id).options(*_LOAD_OPTS)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_servizio(
        self, servizio_id: int, offset: int = 0, limit: int = 20
    ) -> list[Presenza]:
        stmt = (
            select(Presenza)
            .where(Presenza.servizio_id == servizio_id)
            .options(*_LOAD_OPTS)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_servizio(self, servizio_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Presenza)
            .where(Presenza.servizio_id == servizio_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_servizio_con_strumento(self, servizio_id: int) -> list[Presenza]:
        """Organico del servizio con persona.soci/persona.esterni caricati,
        necessari per risalire allo strumento di ciascuna persona (libretto)."""
        stmt = (
            select(Presenza)
            .where(Presenza.servizio_id == servizio_id)
            .options(
                selectinload(Presenza.persona).selectinload(Persona.soci),
                selectinload(Presenza.persona).selectinload(Persona.esterni),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_prova(
        self, prova_id: int, offset: int = 0, limit: int = 20
    ) -> list[Presenza]:
        stmt = (
            select(Presenza)
            .where(Presenza.prova_id == prova_id)
            .options(*_LOAD_OPTS)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_prova(self, prova_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Presenza)
            .where(Presenza.prova_id == prova_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_prova_con_strumento(self, prova_id: int) -> list[Presenza]:
        """Analogo a ``get_by_servizio_con_strumento``, per l'organico di una
        prova."""
        stmt = (
            select(Presenza)
            .where(Presenza.prova_id == prova_id)
            .options(
                selectinload(Presenza.persona).selectinload(Persona.soci),
                selectinload(Presenza.persona).selectinload(Persona.esterni),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_lezione(
        self, lezione_id: int, offset: int = 0, limit: int = 20
    ) -> list[Presenza]:
        stmt = (
            select(Presenza)
            .where(Presenza.lezione_id == lezione_id)
            .options(*_LOAD_OPTS)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_lezione(self, lezione_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Presenza)
            .where(Presenza.lezione_id == lezione_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, data: PresenzaCreate) -> Presenza:
        presenza = Presenza(**data.model_dump())
        self.db.add(presenza)
        await self.db.commit()
        await self.db.refresh(presenza)
        return presenza

    async def update(self, presenza: Presenza, data: PresenzaUpdate) -> Presenza:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(presenza, field, value)
        await self.db.commit()
        await self.db.refresh(presenza)
        return presenza

    async def get_by_ids(self, presenza_ids: list[int]) -> list[Presenza]:
        stmt = (
            select(Presenza).where(Presenza.id.in_(presenza_ids)).options(*_LOAD_OPTS)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def bulk_update(
        self, presenze: list[Presenza], updates: list[PresenzaUpdate]
    ) -> list[Presenza]:
        for presenza, data in zip(presenze, updates, strict=True):
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(presenza, field, value)
        await self.db.commit()
        for presenza in presenze:
            await self.db.refresh(presenza)
        return presenze

    async def delete(self, presenza: Presenza) -> None:
        await self.db.delete(presenza)
        await self.db.commit()
