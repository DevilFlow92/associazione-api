from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions.lookup import LookupNotFoundError
from app.mergefields.base import (
    MergeFieldDefinition,
    MergeFieldProvider,
    format_indirizzo,
)
from app.models.indirizzo import Indirizzo
from app.models.lookups import Banda

_FIELDS = [
    MergeFieldDefinition("descrizione", "Nome banda", "str"),
    MergeFieldDefinition("indirizzo_completo", "Indirizzo", "str"),
]


class BandaProvider(MergeFieldProvider):
    entity_name = "banda"

    def list_fields(self) -> list[MergeFieldDefinition]:
        return _FIELDS

    async def resolve(self, entity_id: int, db: AsyncSession) -> dict:
        stmt = (
            select(Banda)
            .where(Banda.codice == entity_id)
            .options(selectinload(Banda.indirizzi).selectinload(Indirizzo.comune))
        )
        banda = (await db.execute(stmt)).scalar_one_or_none()
        if banda is None:
            raise LookupNotFoundError("Banda", entity_id)

        indirizzo = banda.indirizzi[0] if banda.indirizzi else None

        return {
            "descrizione": banda.descrizione,
            "indirizzo_completo": format_indirizzo(indirizzo),
        }
