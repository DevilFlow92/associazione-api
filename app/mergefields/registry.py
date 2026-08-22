from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.mergefields.base import MergeFieldDefinition, MergeFieldProvider
from app.mergefields.providers.allievo_provider import AllievoProvider
from app.mergefields.providers.banda_provider import BandaProvider
from app.mergefields.providers.contatto_provider import ContattoProvider
from app.mergefields.providers.esterno_provider import EsternoProvider
from app.mergefields.providers.iscrizione_corso_provider import (
    IscrizioneCorsoProvider,
)
from app.mergefields.providers.iscrizione_provider import IscrizioneProvider
from app.mergefields.providers.ricevuta_provider import RicevutaProvider
from app.mergefields.providers.servizio_provider import ServizioProvider
from app.mergefields.providers.socio_provider import SocioProvider

REGISTRY: dict[str, MergeFieldProvider] = {
    provider.entity_name: provider
    for provider in [
        SocioProvider(),
        EsternoProvider(),
        BandaProvider(),
        ContattoProvider(),
        IscrizioneProvider(),
        ServizioProvider(),
        RicevutaProvider(),
        AllievoProvider(),
        IscrizioneCorsoProvider(),
    ]
}


def list_all_fields() -> dict[str, list[MergeFieldDefinition]]:
    return {
        entity_name: provider.list_fields()
        for entity_name, provider in REGISTRY.items()
    }


async def resolve_context(
    entities: dict[str, int], db: AsyncSession
) -> dict[str, dict]:
    """Risolve il valore dei merge field per ogni entità richiesta.

    ``entities`` mappa entity_name -> id (es. ``{"socio": 12, "banda": 1}``).
    Il risultato raggruppa i valori risolti sotto la chiave dell'entità.
    """
    context: dict[str, dict] = {}
    for entity_name, entity_id in entities.items():
        provider = REGISTRY[entity_name]
        context[entity_name] = await provider.resolve(entity_id, db)
    return context
