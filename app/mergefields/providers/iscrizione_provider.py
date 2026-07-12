from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.iscrizione import IscrizioneNotFoundError
from app.mergefields.base import MergeFieldDefinition, MergeFieldProvider
from app.models.lookups import StatoIscrizione
from app.repositories.iscrizione_repository import IscrizioneRepository
from app.repositories.lookup import LookupRepository
from app.utils.export_rendiconto import format_euro

_FIELDS = [
    MergeFieldDefinition("anno", "Anno", "number"),
    MergeFieldDefinition("quota_partecipazione", "Quota partecipazione", "str"),
    MergeFieldDefinition("stato_iscrizione", "Stato iscrizione", "str"),
    MergeFieldDefinition("data_iscrizione", "Data iscrizione", "date"),
    MergeFieldDefinition("note", "Note", "str"),
]


class IscrizioneProvider(MergeFieldProvider):
    entity_name = "iscrizione"

    def list_fields(self) -> list[MergeFieldDefinition]:
        return _FIELDS

    async def resolve(self, entity_id: int, db: AsyncSession) -> dict:
        iscrizione = await IscrizioneRepository(db).get_by_id(entity_id)
        if iscrizione is None:
            raise IscrizioneNotFoundError(entity_id)

        stato = await LookupRepository(db, StatoIscrizione).get_by_codice(
            iscrizione.stato_iscrizione_codice
        )

        return {
            "anno": iscrizione.anno,
            "quota_partecipazione": format_euro(
                Decimal(str(iscrizione.quota_partecipazione))
            ),
            "stato_iscrizione": stato.descrizione if stato else None,
            "data_iscrizione": iscrizione.data_iscrizione,
            "note": iscrizione.note,
        }
