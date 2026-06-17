from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ruolo import Ruolo
from app.models.utente import TipoUtente, Utente


class UtenteRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[Utente]:
        stmt = select(Utente).order_by(Utente.id).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(Utente)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, utente_id: int) -> Utente | None:
        stmt = select(Utente).where(Utente.id == utente_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Utente | None:
        stmt = select(Utente).where(Utente.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        tipo: TipoUtente,
        email: str,
        password_hash: str | None,
        nome_completo: str | None,
        persona_id: int | None,
        superuser: bool,
        ruoli: list[Ruolo],
    ) -> Utente:
        utente = Utente(
            tipo=tipo,
            email=email,
            password_hash=password_hash,
            nome_completo=nome_completo,
            persona_id=persona_id,
            superuser=superuser,
        )
        utente.ruoli = ruoli
        self.db.add(utente)
        await self.db.commit()
        await self.db.refresh(utente)
        return utente

    async def update(
        self,
        utente: Utente,
        *,
        fields: dict,
        ruoli: list[Ruolo] | None,
    ) -> Utente:
        for field, value in fields.items():
            setattr(utente, field, value)
        if ruoli is not None:
            utente.ruoli = ruoli
        await self.db.commit()
        await self.db.refresh(utente)
        return utente

    async def set_password(self, utente: Utente, password_hash: str) -> Utente:
        utente.password_hash = password_hash
        await self.db.commit()
        await self.db.refresh(utente)
        return utente

    async def delete(self, utente: Utente) -> None:
        await self.db.delete(utente)
        await self.db.commit()
