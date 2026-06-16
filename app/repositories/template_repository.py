from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.template import Template
from app.schemas.template import TemplateCreate, TemplateUpdate


class TemplateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        documento_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        stmt = select(Template)
        if documento_id is not None:
            stmt = stmt.where(Template.documento_id == documento_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self, documento_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Template)
        if documento_id is not None:
            stmt = stmt.where(Template.documento_id == documento_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, template_id: int) -> Template | None:
        stmt = select(Template).where(Template.id == template_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_documento(self, template_id: int) -> Template | None:
        stmt = (
            select(Template)
            .where(Template.id == template_id)
            .options(selectinload(Template.documento))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: TemplateCreate) -> Template:
        template = Template(**data.model_dump())
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
