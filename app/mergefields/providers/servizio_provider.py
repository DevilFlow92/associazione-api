from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.servizio import ServizioNotFoundError
from app.mergefields.base import (
    MergeFieldDefinition,
    MergeFieldProvider,
    format_indirizzo,
)
from app.repositories.servizio_repository import ServizioRepository

_FIELDS = [
    MergeFieldDefinition("descrizione_servizio", "Descrizione servizio", "str"),
    MergeFieldDefinition("data_servizio", "Data servizio", "date"),
    MergeFieldDefinition("indirizzo_completo", "Indirizzo", "str"),
    MergeFieldDefinition("anno", "Anno", "number"),
    MergeFieldDefinition("note", "Note", "str"),
]


class ServizioProvider(MergeFieldProvider):
    entity_name = "servizio"

    def list_fields(self) -> list[MergeFieldDefinition]:
        return _FIELDS

    async def resolve(self, entity_id: int, db: AsyncSession) -> dict:
        servizio = await ServizioRepository(db).get_by_id(entity_id)
        if servizio is None:
            raise ServizioNotFoundError(entity_id)

        return {
            "descrizione_servizio": servizio.descrizione_servizio,
            "data_servizio": servizio.data_servizio,
            "indirizzo_completo": format_indirizzo(servizio.indirizzo),
            "anno": servizio.anno,
            "note": servizio.note,
        }
