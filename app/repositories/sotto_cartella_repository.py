from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.macro_sezione import MacroSezione
from app.models.sotto_cartella import SottoCartella


class MacroSezioneRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> list[MacroSezione]:
        stmt = select(MacroSezione).order_by(MacroSezione.ordine)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_codice(self, codice: int) -> MacroSezione | None:
        stmt = select(MacroSezione).where(MacroSezione.codice == codice)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class SottoCartellaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: int) -> SottoCartella | None:
        stmt = select(SottoCartella).where(SottoCartella.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_macro_sezione(
        self, macro_sezione_codice: int
    ) -> list[SottoCartella]:
        stmt = (
            select(SottoCartella)
            .where(SottoCartella.macro_sezione_codice == macro_sezione_codice)
            .order_by(SottoCartella.nome)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_nome(
        self, nome: str, macro_sezione_codice: int
    ) -> SottoCartella | None:
        stmt = select(SottoCartella).where(
            SottoCartella.nome == nome,
            SottoCartella.macro_sezione_codice == macro_sezione_codice,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, nome: str, macro_sezione_codice: int) -> SottoCartella:
        obj = SottoCartella(nome=nome, macro_sezione_codice=macro_sezione_codice)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: SottoCartella, nome: str) -> SottoCartella:
        obj.nome = nome
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: SottoCartella) -> None:
        await self.db.delete(obj)
        await self.db.commit()
