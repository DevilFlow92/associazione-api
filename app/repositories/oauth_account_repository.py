from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.oauth_account import OAuthAccount
from app.models.utente import Utente


class OAuthAccountRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_provider(
        self, provider: str, provider_user_id: str
    ) -> OAuthAccount | None:
        result = await self.db.execute(
            select(OAuthAccount)
            .where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
            .options(selectinload(OAuthAccount.utente).selectinload(Utente.ruoli))
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        utente_id: int,
        provider: str,
        provider_user_id: str,
        email: str | None,
    ) -> OAuthAccount:
        account = OAuthAccount(
            utente_id=utente_id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
        )
        self.db.add(account)
        await self.db.flush()
        return account
