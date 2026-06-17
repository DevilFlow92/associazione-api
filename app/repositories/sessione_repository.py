from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sessione import Sessione


class SessioneRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, utente_id: int, token_hash: str, scade_il: datetime
    ) -> Sessione:
        sessione = Sessione(
            utente_id=utente_id, token_hash=token_hash, scade_il=scade_il
        )
        self.db.add(sessione)
        await self.db.commit()
        await self.db.refresh(sessione)
        return sessione

    async def get_by_token_hash(self, token_hash: str) -> Sessione | None:
        stmt = select(Sessione).where(Sessione.token_hash == token_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, sessione: Sessione, *, at: datetime) -> None:
        sessione.revocata_il = at
        await self.db.commit()
