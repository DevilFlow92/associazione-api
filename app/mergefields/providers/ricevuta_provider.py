from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.ricevuta import RicevutaNotFoundError
from app.mergefields.base import MergeFieldDefinition, MergeFieldProvider
from app.repositories.ricevuta_repository import RicevutaRepository
from app.utils.export_rendiconto import format_euro

_FIELDS = [
    MergeFieldDefinition("data_ricevuta", "Data ricevuta", "date"),
    MergeFieldDefinition("importo", "Importo", "str"),
    MergeFieldDefinition("note_in_stampa", "Note in stampa", "str"),
]


class RicevutaProvider(MergeFieldProvider):
    entity_name = "ricevuta"

    def list_fields(self) -> list[MergeFieldDefinition]:
        return _FIELDS

    async def resolve(self, entity_id: int, db: AsyncSession) -> dict:
        ricevuta = await RicevutaRepository(db).get_by_id(entity_id)
        if ricevuta is None:
            raise RicevutaNotFoundError(entity_id)

        return {
            "data_ricevuta": ricevuta.data_ricevuta,
            "importo": format_euro(Decimal(str(ricevuta.importo))),
            "note_in_stampa": ricevuta.note_in_stampa,
        }
