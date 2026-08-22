from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.allievo import AllievoNotFoundError
from app.mergefields.base import (
    MergeFieldDefinition,
    MergeFieldProvider,
    format_indirizzo,
)
from app.repositories.allievo_repository import AllievoRepository

_FIELDS = [
    MergeFieldDefinition("codice_allievo", "Codice allievo", "str"),
    MergeFieldDefinition("nome", "Nome", "str"),
    MergeFieldDefinition("cognome", "Cognome", "str"),
    MergeFieldDefinition("codice_fiscale", "Codice fiscale", "str"),
    MergeFieldDefinition("data_nascita", "Data di nascita", "date"),
    MergeFieldDefinition("indirizzo_completo", "Indirizzo", "str"),
]


class AllievoProvider(MergeFieldProvider):
    entity_name = "allievo"

    def list_fields(self) -> list[MergeFieldDefinition]:
        return _FIELDS

    async def resolve(self, entity_id: int, db: AsyncSession) -> dict:
        allievo = await AllievoRepository(db).get_by_id(entity_id)
        if allievo is None:
            raise AllievoNotFoundError(entity_id)

        return {
            "codice_allievo": allievo.codice_allievo,
            "nome": allievo.persona.nome,
            "cognome": allievo.persona.cognome,
            "codice_fiscale": allievo.persona.codice_fiscale,
            "data_nascita": allievo.persona.data_nascita,
            "indirizzo_completo": format_indirizzo(allievo.indirizzo),
        }
