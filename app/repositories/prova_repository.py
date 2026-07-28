from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.indirizzo import Indirizzo
from app.models.lookups import Comune
from app.models.prova import Prova
from app.schemas.prova import ProvaCreate, ProvaUpdate

_LOAD_OPTS = [
    selectinload(Prova.indirizzo)
    .selectinload(Indirizzo.comune)
    .selectinload(Comune.provincia),
    selectinload(Prova.servizio),
]


class ProvaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        banda_codice: int | None = None,
        servizio_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Prova]:
        stmt = select(Prova).options(*_LOAD_OPTS)
        if banda_codice is not None:
            stmt = stmt.where(Prova.banda_codice == banda_codice)
        if servizio_id is not None:
            stmt = stmt.where(Prova.servizio_id == servizio_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self, banda_codice: int | None = None, servizio_id: int | None = None
    ) -> int:
        stmt = select(func.count()).select_from(Prova)
        if banda_codice is not None:
            stmt = stmt.where(Prova.banda_codice == banda_codice)
        if servizio_id is not None:
            stmt = stmt.where(Prova.servizio_id == servizio_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, prova_id: int) -> Prova | None:
        stmt = select(Prova).where(Prova.id == prova_id).options(*_LOAD_OPTS)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: ProvaCreate) -> Prova:
        prova = Prova(**data.model_dump())
        self.db.add(prova)
        await self.db.flush()
        prova_id = prova.id
        await self.db.commit()
        result = await self.get_by_id(prova_id)
        assert result is not None
        return result

    async def update(self, prova: Prova, data: ProvaUpdate) -> Prova:
        prova_id = prova.id
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(prova, field, value)
        await self.db.commit()
        # La sessione usa expire_on_commit=False: senza expire esplicito
        # l'istanza resta nell'identity map con le relazioni caricate *prima*
        # dell'update, e ``get_by_id`` non le sovrascriverebbe. La risposta
        # conterrebbe così un ``indirizzo``/``servizio`` stantio rispetto alla
        # FK appena scritta (es. null su una prova a cui l'indirizzo è stato
        # appena assegnato).
        self.db.expire(prova)
        result = await self.get_by_id(prova_id)
        assert result is not None
        return result

    async def delete(self, prova: Prova) -> None:
        await self.db.delete(prova)
        await self.db.commit()
