from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.socio import SocioNotFoundError
from app.mergefields.base import (
    MergeFieldDefinition,
    MergeFieldProvider,
    format_indirizzo,
)
from app.repositories.persona_repository import PersonaRepository
from app.repositories.socio_repository import SocioRepository

_FIELDS = [
    MergeFieldDefinition("codice_socio", "Codice socio", "str"),
    MergeFieldDefinition("nome", "Nome", "str"),
    MergeFieldDefinition("cognome", "Cognome", "str"),
    MergeFieldDefinition("codice_fiscale", "Codice fiscale", "str"),
    MergeFieldDefinition("data_nascita", "Data di nascita", "date"),
    MergeFieldDefinition("indirizzo_completo", "Indirizzo", "str"),
]


class SocioProvider(MergeFieldProvider):
    entity_name = "socio"

    def list_fields(self) -> list[MergeFieldDefinition]:
        return _FIELDS

    async def resolve(self, entity_id: int, db: AsyncSession) -> dict:
        socio = await SocioRepository(db).get_by_id(entity_id)
        if socio is None:
            raise SocioNotFoundError(entity_id)

        persona = await PersonaRepository(db).get_with_indirizzi(socio.persona.id)
        indirizzo = persona.indirizzi[0] if persona and persona.indirizzi else None

        return {
            "codice_socio": socio.codice_socio,
            "nome": socio.persona.nome,
            "cognome": socio.persona.cognome,
            "codice_fiscale": socio.persona.codice_fiscale,
            "data_nascita": socio.persona.data_nascita,
            "indirizzo_completo": format_indirizzo(indirizzo),
        }
