from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.documento import Documento, TipoDocumento


class DocumentoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        tipo: TipoDocumento | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Documento]:
        stmt = select(Documento)
        if tipo:
            stmt = stmt.where(Documento.tipo == tipo)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, tipo: TipoDocumento | None = None) -> int:
        stmt = select(func.count()).select_from(Documento)
        if tipo:
            stmt = stmt.where(Documento.tipo == tipo)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, documento_id: int) -> Documento | None:
        stmt = select(Documento).where(Documento.id == documento_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_socio(self, socio_id: int) -> list[Documento]:
        stmt = select(Documento).where(Documento.socio_id == socio_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        nome: str,
        tipo: TipoDocumento,
        file_path: str,
        mime_type: str,
        dimensione_bytes: int,
        checksum: str,
        socio_id: int | None = None,
        note: str | None = None,
    ) -> Documento:
        documento = Documento(
            nome=nome,
            tipo=tipo,
            file_path=file_path,
            mime_type=mime_type,
            dimensione_bytes=dimensione_bytes,
            checksum=checksum,
            socio_id=socio_id,
            note=note,
        )
        self.db.add(documento)
        await self.db.commit()
        await self.db.refresh(documento)
        return documento

    async def delete(self, documento: Documento) -> None:
        await self.db.delete(documento)
        await self.db.commit()
