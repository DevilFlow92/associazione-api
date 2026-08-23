from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.voce_programma_catalogo import VoceProgrammaCatalogo
from app.schemas.voce_programma_catalogo import (
    VoceProgrammaCatalogoCreate,
    VoceProgrammaCatalogoUpdate,
)

_LOAD_OPTS = [
    selectinload(VoceProgrammaCatalogo.tipo_corso),
    selectinload(VoceProgrammaCatalogo.categoria),
]


class VoceProgrammaCatalogoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        tipo_corso_codice: int | None = None,
        categoria_codice: int | None = None,
        livello: int | None = None,
        attiva: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[VoceProgrammaCatalogo]:
        stmt = select(VoceProgrammaCatalogo).options(*_LOAD_OPTS)
        if tipo_corso_codice is not None:
            stmt = stmt.where(
                VoceProgrammaCatalogo.tipo_corso_codice == tipo_corso_codice
            )
        if categoria_codice is not None:
            stmt = stmt.where(
                VoceProgrammaCatalogo.categoria_codice == categoria_codice
            )
        if livello is not None:
            stmt = stmt.where(VoceProgrammaCatalogo.livello == livello)
        if attiva is not None:
            stmt = stmt.where(VoceProgrammaCatalogo.attiva == attiva)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        tipo_corso_codice: int | None = None,
        categoria_codice: int | None = None,
        livello: int | None = None,
        attiva: bool | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(VoceProgrammaCatalogo)
        if tipo_corso_codice is not None:
            stmt = stmt.where(
                VoceProgrammaCatalogo.tipo_corso_codice == tipo_corso_codice
            )
        if categoria_codice is not None:
            stmt = stmt.where(
                VoceProgrammaCatalogo.categoria_codice == categoria_codice
            )
        if livello is not None:
            stmt = stmt.where(VoceProgrammaCatalogo.livello == livello)
        if attiva is not None:
            stmt = stmt.where(VoceProgrammaCatalogo.attiva == attiva)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, voce_id: int) -> VoceProgrammaCatalogo | None:
        stmt = (
            select(VoceProgrammaCatalogo)
            .where(VoceProgrammaCatalogo.id == voce_id)
            .options(*_LOAD_OPTS)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_tipo_corso_e_testo(
        self, tipo_corso_codice: int, testo: str
    ) -> VoceProgrammaCatalogo | None:
        stmt = select(VoceProgrammaCatalogo).where(
            VoceProgrammaCatalogo.tipo_corso_codice == tipo_corso_codice,
            VoceProgrammaCatalogo.testo == testo,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: VoceProgrammaCatalogoCreate) -> VoceProgrammaCatalogo:
        voce = VoceProgrammaCatalogo(**data.model_dump())
        self.db.add(voce)
        await self.db.flush()
        voce_id = voce.id
        await self.db.commit()
        result = await self.get_by_id(voce_id)
        assert result is not None
        return result

    async def update(
        self, voce: VoceProgrammaCatalogo, data: VoceProgrammaCatalogoUpdate
    ) -> VoceProgrammaCatalogo:
        voce_id = voce.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(voce, field, value)
        await self.db.commit()
        self.db.expire(voce)
        result = await self.get_by_id(voce_id)
        assert result is not None
        return result
