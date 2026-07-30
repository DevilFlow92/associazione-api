from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pagamento_corso import PagamentoCorso
from app.schemas.pagamento_corso import PagamentoCorsoUpdate

_LOAD_OPTS = [
    selectinload(PagamentoCorso.ricevuta),
]


class PagamentoCorsoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        iscrizione_corso_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[PagamentoCorso]:
        stmt = select(PagamentoCorso).options(*_LOAD_OPTS)
        if iscrizione_corso_id is not None:
            stmt = stmt.where(PagamentoCorso.iscrizione_corso_id == iscrizione_corso_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, iscrizione_corso_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(PagamentoCorso)
        if iscrizione_corso_id is not None:
            stmt = stmt.where(PagamentoCorso.iscrizione_corso_id == iscrizione_corso_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, pagamento_corso_id: int) -> PagamentoCorso | None:
        stmt = (
            select(PagamentoCorso)
            .where(PagamentoCorso.id == pagamento_corso_id)
            .options(*_LOAD_OPTS)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ── Operazioni transazionali (commit gestito dal service) ────────────────
    def add_no_commit(self, pagamento: PagamentoCorso) -> None:
        self.db.add(pagamento)

    def update_no_commit(
        self, pagamento: PagamentoCorso, data: PagamentoCorsoUpdate
    ) -> None:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(pagamento, field, value)

    async def delete_no_commit(self, pagamento: PagamentoCorso) -> None:
        await self.db.delete(pagamento)

    async def flush(self) -> None:
        await self.db.flush()

    async def commit(self) -> None:
        await self.db.commit()

    async def refresh(self, pagamento: PagamentoCorso) -> None:
        await self.db.refresh(pagamento)
