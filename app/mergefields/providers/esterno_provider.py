from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.esterno import EsternoNotFoundError
from app.mergefields.base import (
    MergeFieldDefinition,
    MergeFieldProvider,
    format_indirizzo,
)
from app.repositories.esterno_repository import EsternoRepository
from app.repositories.persona_repository import PersonaRepository

_FIELDS = [
    MergeFieldDefinition("codice_esterno", "Codice esterno", "str"),
    MergeFieldDefinition("nome", "Nome", "str"),
    MergeFieldDefinition("cognome", "Cognome", "str"),
    MergeFieldDefinition("codice_fiscale", "Codice fiscale", "str"),
    MergeFieldDefinition("data_nascita", "Data di nascita", "date"),
    MergeFieldDefinition("indirizzo_completo", "Indirizzo", "str"),
    MergeFieldDefinition("ragione_sociale", "Ragione sociale", "str"),
    MergeFieldDefinition("luogo_nascita", "Luogo di nascita", "str"),
    MergeFieldDefinition("strumento", "Strumento", "str"),
]


class EsternoProvider(MergeFieldProvider):
    entity_name = "esterno"

    def list_fields(self) -> list[MergeFieldDefinition]:
        return _FIELDS

    async def resolve(self, entity_id: int, db: AsyncSession) -> dict:
        esterno = await EsternoRepository(db).get_by_id(entity_id)
        if esterno is None:
            raise EsternoNotFoundError(entity_id)

        persona = await PersonaRepository(db).get_with_indirizzi(esterno.persona.id)
        indirizzo = persona.indirizzi[0] if persona and persona.indirizzi else None
        comune_nascita = esterno.persona.comune_nascita

        return {
            "codice_esterno": esterno.codice_esterno,
            "nome": esterno.persona.nome,
            "cognome": esterno.persona.cognome,
            "codice_fiscale": esterno.persona.codice_fiscale,
            "data_nascita": esterno.persona.data_nascita,
            "indirizzo_completo": format_indirizzo(indirizzo),
            "ragione_sociale": esterno.persona.ragione_sociale,
            "luogo_nascita": comune_nascita.descrizione if comune_nascita else None,
            "strumento": esterno.strumento.descrizione,
        }
