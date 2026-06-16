from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.indirizzo import Indirizzo
from app.models.lookups import Banda


class BandaIndirizzoRepository:
    """Gestione della relazione molti-a-molti banda↔indirizzo."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_with_indirizzi(self, banda_codice: int) -> Banda | None:
        stmt = (
            select(Banda)
            .where(Banda.codice == banda_codice)
            .options(selectinload(Banda.indirizzi))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_indirizzo(self, banda: Banda, indirizzo: Indirizzo) -> None:
        """Collega un indirizzo alla banda (idempotente).

        ``banda`` deve essere caricata con ``get_with_indirizzi``.
        """
        if indirizzo not in banda.indirizzi:
            banda.indirizzi.append(indirizzo)
            await self.db.commit()

    async def remove_indirizzo(self, banda: Banda, indirizzo: Indirizzo) -> None:
        """Scollega un indirizzo dalla banda (idempotente)."""
        if indirizzo in banda.indirizzi:
            banda.indirizzi.remove(indirizzo)
            await self.db.commit()
