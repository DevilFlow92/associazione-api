from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.indirizzo import Indirizzo
from app.models.persona import Persona
from app.schemas.persona import PersonaCreate, PersonaUpdate


class PersonaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[Persona]:
        stmt = select(Persona).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(Persona)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, persona_id: int) -> Persona | None:
        stmt = select(Persona).where(Persona.id == persona_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_indirizzi(self, persona_id: int) -> Persona | None:
        stmt = (
            select(Persona)
            .where(Persona.id == persona_id)
            .options(selectinload(Persona.indirizzi))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: PersonaCreate) -> Persona:
        persona = Persona(**data.model_dump())
        self.db.add(persona)
        await self.db.commit()
        await self.db.refresh(persona)
        return persona

    async def update(self, persona: Persona, data: PersonaUpdate) -> Persona:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(persona, field, value)
        await self.db.commit()
        await self.db.refresh(persona)
        return persona

    async def has_dependents(self, persona_id: int) -> bool:
        """True se la persona è collegata a un socio o a un esterno."""
        from app.models.esterno import Esterno
        from app.models.socio import Socio

        stmt = (
            select(func.count())
            .select_from(Socio)
            .where(Socio.persona_id == persona_id)
        )
        soci = (await self.db.execute(stmt)).scalar_one()
        stmt = (
            select(func.count())
            .select_from(Esterno)
            .where(Esterno.persona_id == persona_id)
        )
        esterni = (await self.db.execute(stmt)).scalar_one()
        return bool(soci or esterni)

    async def delete(self, persona_id: int) -> None:
        """Elimina la persona e i figli posseduti (contatti, indirizzi collegati).

        Le collezioni vengono caricate esplicitamente prima di ``delete`` così
        che la cascata avvenga in memoria, senza lazy-load (vietato in async).
        Da chiamare solo dopo aver verificato l'assenza di dipendenti.
        """
        stmt = (
            select(Persona)
            .where(Persona.id == persona_id)
            .options(
                selectinload(Persona.contatti),
                selectinload(Persona.indirizzi),
            )
        )
        persona = (await self.db.execute(stmt)).scalar_one_or_none()
        if persona is None:
            return
        await self.db.delete(persona)
        await self.db.commit()

    async def add_indirizzo(self, persona: Persona, indirizzo: Indirizzo) -> None:
        """Collega un indirizzo alla persona (idempotente).

        ``persona`` deve essere caricata con ``get_with_indirizzi``.
        """
        if indirizzo not in persona.indirizzi:
            persona.indirizzi.append(indirizzo)
            await self.db.commit()

    async def remove_indirizzo(self, persona: Persona, indirizzo: Indirizzo) -> None:
        """Scollega un indirizzo dalla persona (idempotente)."""
        if indirizzo in persona.indirizzi:
            persona.indirizzi.remove(indirizzo)
            await self.db.commit()
