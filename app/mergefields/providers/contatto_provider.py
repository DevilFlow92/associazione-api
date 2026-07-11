from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.contatto import ContattoNotFoundError
from app.mergefields.base import MergeFieldDefinition, MergeFieldProvider
from app.models.lookups import RuoloContatto
from app.repositories.contatto_repository import ContattoRepository
from app.repositories.lookup import LookupRepository

_FIELDS = [
    MergeFieldDefinition("email", "Email", "str"),
    MergeFieldDefinition("telefono", "Telefono", "str"),
    MergeFieldDefinition("ruolo_contatto", "Ruolo contatto", "str"),
]


class ContattoProvider(MergeFieldProvider):
    entity_name = "contatto"

    def list_fields(self) -> list[MergeFieldDefinition]:
        return _FIELDS

    async def resolve(self, entity_id: int, db: AsyncSession) -> dict:
        contatto = await ContattoRepository(db).get_by_id(entity_id)
        if contatto is None:
            raise ContattoNotFoundError(entity_id)

        ruolo = await LookupRepository(db, RuoloContatto).get_by_codice(
            contatto.ruolo_contatto_codice
        )

        return {
            "email": contatto.email,
            "telefono": contatto.telefono,
            "ruolo_contatto": ruolo.descrizione if ruolo else None,
        }
