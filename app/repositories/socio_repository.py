from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.socio import Socio, StatoSocio
from app.schemas.socio import SocioCreate, SocioUpdate


class SocioRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, include_deleted: bool = False) -> list[Socio]:
        stmt = select(Socio)
        if not include_deleted:
            stmt = stmt.where(Socio.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, socio_id: int) -> Socio | None:
        stmt = select(Socio).where(Socio.id == socio_id, Socio.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Socio | None:
        stmt = select(Socio).where(Socio.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: SocioCreate) -> Socio:
        socio = Socio(**data.model_dump())
        self.db.add(socio)
        await self.db.commit()
        await self.db.refresh(socio)
        return socio

    async def update(self, socio: Socio, data: SocioUpdate) -> Socio:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(socio, field, value)
        await self.db.commit()
        await self.db.refresh(socio)
        return socio

    async def soft_delete(self, socio: Socio) -> Socio:
        from datetime import date

        socio.deleted_at = date.today()
        socio.stato = StatoSocio.CESSATO
        await self.db.commit()
        return socio
