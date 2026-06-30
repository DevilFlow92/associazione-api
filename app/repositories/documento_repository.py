from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.documento import Documento

_LOAD_OPTS = [
    selectinload(Documento.tipo_documento),
    selectinload(Documento.sotto_cartella),
]


class DocumentoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        tipo_documento_codice: int | None = None,
        sotto_cartella_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Documento]:
        stmt = select(Documento).options(*_LOAD_OPTS)
        if tipo_documento_codice is not None:
            stmt = stmt.where(Documento.tipo_documento_codice == tipo_documento_codice)
        if sotto_cartella_id is not None:
            stmt = stmt.where(Documento.sotto_cartella_id == sotto_cartella_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        tipo_documento_codice: int | None = None,
        sotto_cartella_id: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Documento)
        if tipo_documento_codice is not None:
            stmt = stmt.where(Documento.tipo_documento_codice == tipo_documento_codice)
        if sotto_cartella_id is not None:
            stmt = stmt.where(Documento.sotto_cartella_id == sotto_cartella_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, documento_id: int) -> Documento | None:
        stmt = (
            select(Documento).where(Documento.id == documento_id).options(*_LOAD_OPTS)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        nome: str,
        file_path: str,
        mime_type: str,
        dimensione_bytes: int,
        checksum: str,
        tipo_documento_codice: int | None = None,
        sotto_cartella_id: int | None = None,
        note: str | None = None,
    ) -> Documento:
        documento = Documento(
            nome=nome,
            file_path=file_path,
            mime_type=mime_type,
            dimensione_bytes=dimensione_bytes,
            checksum=checksum,
            tipo_documento_codice=tipo_documento_codice,
            sotto_cartella_id=sotto_cartella_id,
            note=note,
        )
        self.db.add(documento)
        await self.db.flush()
        documento_id = documento.id
        await self.db.commit()
        result = await self.get_by_id(documento_id)
        assert result is not None
        return result

    async def delete(self, documento: Documento) -> None:
        await self.db.delete(documento)
        await self.db.commit()
