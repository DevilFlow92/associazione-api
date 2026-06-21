from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.iscrizione import Iscrizione
from app.models.lookups import StatoIscrizione
from app.models.persona import Persona
from app.models.socio import Socio
from app.schemas.iscrizione import IscrizioneCreate, IscrizioneUpdate


def _with_rels():
    return select(Iscrizione).options(
        selectinload(Iscrizione.socio).selectinload(Socio.persona)
    )


class IscrizioneRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        socio_id: int | None = None,
        anno: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Iscrizione]:
        stmt = select(Iscrizione)
        if socio_id is not None:
            stmt = stmt.where(Iscrizione.socio_id == socio_id)
        if anno is not None:
            stmt = stmt.where(Iscrizione.anno == anno)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        socio_id: int | None = None,
        anno: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Iscrizione)
        if socio_id is not None:
            stmt = stmt.where(Iscrizione.socio_id == socio_id)
        if anno is not None:
            stmt = stmt.where(Iscrizione.anno == anno)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, iscrizione_id: int) -> Iscrizione | None:
        stmt = _with_rels().where(Iscrizione.id == iscrizione_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_quote_versate_per_anno(
        self, banda_codice: int, anno: int
    ) -> dict[int, Decimal]:
        """Somma delle quote pagate per socio nell'anno indicato.

        Considera solo le iscrizioni con stato ``Pagata`` (match
        case-insensitive sulla descrizione) dei soci appartenenti alla banda.
        Restituisce ``{socio_id: totale_quota_pagata}``.
        """
        stmt = (
            select(
                Iscrizione.socio_id,
                func.sum(Iscrizione.quota_partecipazione),
            )
            .join(Socio, Iscrizione.socio_id == Socio.id)
            .join(Persona, Socio.persona_id == Persona.id)
            .join(
                StatoIscrizione,
                Iscrizione.stato_iscrizione_codice == StatoIscrizione.codice,
            )
            .where(
                Iscrizione.anno == anno,
                Persona.banda_codice == banda_codice,
                func.lower(StatoIscrizione.descrizione) == "pagata",
            )
            .group_by(Iscrizione.socio_id)
        )
        result = await self.db.execute(stmt)
        return {
            socio_id: Decimal(str(totale))
            for socio_id, totale in result
            if totale is not None
        }

    async def create(self, data: IscrizioneCreate) -> Iscrizione:
        iscrizione = Iscrizione(**data.model_dump())
        self.db.add(iscrizione)
        await self.db.commit()
        await self.db.refresh(iscrizione)
        return iscrizione

    async def update(
        self, iscrizione: Iscrizione, data: IscrizioneUpdate
    ) -> Iscrizione:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(iscrizione, field, value)
        await self.db.commit()
        await self.db.refresh(iscrizione)
        return iscrizione

    async def delete(self, iscrizione: Iscrizione) -> None:
        await self.db.delete(iscrizione)
        await self.db.commit()

    # ── Operazioni transazionali (commit gestito dal service) ────────────────
    def add_no_commit(self, iscrizione: Iscrizione) -> None:
        self.db.add(iscrizione)

    def update_no_commit(self, iscrizione: Iscrizione, data: IscrizioneUpdate) -> None:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(iscrizione, field, value)

    async def delete_no_commit(self, iscrizione: Iscrizione) -> None:
        await self.db.delete(iscrizione)

    async def flush(self) -> None:
        await self.db.flush()

    async def commit(self) -> None:
        await self.db.commit()

    async def refresh(self, iscrizione: Iscrizione) -> None:
        await self.db.refresh(iscrizione)
