from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.mergefields.base import MergeFieldDefinition, MergeFieldProvider
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository

_FIELDS = [
    MergeFieldDefinition("data_iscrizione", "Data iscrizione", "date"),
    MergeFieldDefinition("note", "Note", "str"),
    MergeFieldDefinition("stato_iscrizione_corso", "Stato iscrizione corso", "str"),
    MergeFieldDefinition("tipo_corso", "Tipo corso", "str"),
    MergeFieldDefinition("anno_corso", "Anno corso", "number"),
]


class IscrizioneCorsoProvider(MergeFieldProvider):
    entity_name = "iscrizione_corso"

    def list_fields(self) -> list[MergeFieldDefinition]:
        return _FIELDS

    async def resolve(self, entity_id: int, db: AsyncSession) -> dict:
        iscrizione_corso = await IscrizioneCorsoRepository(db).get_by_id(entity_id)
        if iscrizione_corso is None:
            raise IscrizioneCorsoNotFoundError(entity_id)

        return {
            "data_iscrizione": iscrizione_corso.data_iscrizione,
            "note": iscrizione_corso.note,
            "stato_iscrizione_corso": (
                iscrizione_corso.stato_iscrizione_corso.descrizione
            ),
            "tipo_corso": iscrizione_corso.corso.tipo_corso.descrizione,
            "anno_corso": iscrizione_corso.corso.anno,
        }
