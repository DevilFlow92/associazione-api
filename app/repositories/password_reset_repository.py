from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken


class PasswordResetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def create(self, utente_id: int, token: str, scade_il: datetime) -> None:
        record = PasswordResetToken(
            utente_id=utente_id,
            token_hash=self._hash(token),
            scade_il=scade_il,
        )
        self.db.add(record)
        await self.db.commit()

    async def consume(self, token: str) -> PasswordResetToken | None:
        """Restituisce il token se valido (non scaduto, non usato) e lo marca usato."""
        token_hash = self._hash(token)
        now = datetime.now(UTC)
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.usato_il.is_(None),
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        # Lo scade_il letto da SQLite può tornare naive: confronto in UTC.
        scade_il = record.scade_il
        if scade_il.tzinfo is None:
            scade_il = scade_il.replace(tzinfo=UTC)
        if scade_il <= now:
            return None
        record.usato_il = now
        await self.db.commit()
        return record
