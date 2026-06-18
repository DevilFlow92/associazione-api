from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.persona import Persona
from app.models.socio import Socio
from app.schemas.socio import SocioCreate, SocioUpdate

_PERSONA_OPTS = selectinload(Socio.persona).selectinload(Persona.comune_nascita)


class SocioRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self, offset: int = 0, limit: int = 20, banda_codice: int | None = None
    ) -> list[Socio]:
        stmt = select(Socio).options(_PERSONA_OPTS)
        if banda_codice is not None:
            stmt = stmt.where(Socio.banda_codice == banda_codice)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, banda_codice: int | None = None) -> int:
        stmt = select(func.count()).select_from(Socio)
        if banda_codice is not None:
            stmt = stmt.where(Socio.banda_codice == banda_codice)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, socio_id: int) -> Socio | None:
        stmt = select(Socio).where(Socio.id == socio_id).options(_PERSONA_OPTS)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_codice(self, codice_socio: str, banda_codice: int) -> Socio | None:
        stmt = select(Socio).where(
            Socio.codice_socio == codice_socio,
            Socio.banda_codice == banda_codice,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: SocioCreate) -> Socio:
        socio = Socio(**data.model_dump())
        self.db.add(socio)
        await self.db.flush()
        socio_id = socio.id
        await self.db.commit()
        result = await self.get_by_id(socio_id)
        assert result is not None
        return result

    async def update(self, socio: Socio, data: SocioUpdate) -> Socio:
        socio_id = socio.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(socio, field, value)
        await self.db.commit()
        result = await self.get_by_id(socio_id)
        assert result is not None
        return result

    async def delete(self, socio: Socio) -> None:
        await self.db.delete(socio)
        await self.db.commit()
