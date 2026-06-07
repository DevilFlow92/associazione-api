from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template, TipoTemplate
from app.schemas.template import TemplateUpdate


class TemplateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        tipo: TipoTemplate | None = None,
        solo_attivi: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        stmt = select(Template)
        if tipo:
            stmt = stmt.where(Template.tipo == tipo)
        if solo_attivi:
            stmt = stmt.where(Template.attivo.is_(True))
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        tipo: TipoTemplate | None = None,
        solo_attivi: bool = True,
    ) -> int:
        stmt = select(func.count()).select_from(Template)
        if tipo:
            stmt = stmt.where(Template.tipo == tipo)
        if solo_attivi:
            stmt = stmt.where(Template.attivo.is_(True))
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, template_id: int) -> Template | None:
        stmt = select(Template).where(Template.id == template_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        nome: str,
        tipo: TipoTemplate,
        file_path: str,
        mime_type: str,
        dimensione_bytes: int,
        checksum: str,
        descrizione: str | None = None,
    ) -> Template:
        template = Template(
            nome=nome,
            tipo=tipo,
            file_path=file_path,
            mime_type=mime_type,
            dimensione_bytes=dimensione_bytes,
            checksum=checksum,
            descrizione=descrizione,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update(self, template: Template, data: TemplateUpdate) -> Template:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(template, field, value)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete(self, template: Template) -> None:
        await self.db.delete(template)
        await self.db.commit()
