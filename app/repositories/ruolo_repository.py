from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permesso import Permesso
from app.models.ruolo import Ruolo


class RuoloRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[Ruolo]:
        stmt = select(Ruolo).order_by(Ruolo.id).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(Ruolo)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, ruolo_id: int) -> Ruolo | None:
        stmt = select(Ruolo).where(Ruolo.id == ruolo_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_nome(self, nome: str, banda_codice: int | None) -> Ruolo | None:
        stmt = select(Ruolo).where(
            Ruolo.nome == nome, Ruolo.banda_codice.is_not_distinct_from(banda_codice)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        nome: str,
        descrizione: str | None,
        banda_codice: int | None,
        permessi: list[Permesso],
    ) -> Ruolo:
        ruolo = Ruolo(nome=nome, descrizione=descrizione, banda_codice=banda_codice)
        ruolo.permessi = permessi
        self.db.add(ruolo)
        await self.db.commit()
        await self.db.refresh(ruolo)
        return ruolo

    async def update(
        self,
        ruolo: Ruolo,
        *,
        fields: dict,
        permessi: list[Permesso] | None,
    ) -> Ruolo:
        for field, value in fields.items():
            setattr(ruolo, field, value)
        if permessi is not None:
            ruolo.permessi = permessi
        await self.db.commit()
        await self.db.refresh(ruolo)
        return ruolo

    async def delete(self, ruolo: Ruolo) -> None:
        await self.db.delete(ruolo)
        await self.db.commit()
