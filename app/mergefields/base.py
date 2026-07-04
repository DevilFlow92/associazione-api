from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.indirizzo import Indirizzo

MergeFieldType = Literal["str", "date", "number"]


@dataclass(frozen=True)
class MergeFieldDefinition:
    chiave: str
    etichetta: str
    tipo: MergeFieldType


class MergeFieldProvider(ABC):
    """Espone i campi di un'entità utilizzabili come merge field nei template
    di Modulistica (es. ``{{socio.nome}}``)."""

    entity_name: str

    @abstractmethod
    def list_fields(self) -> list[MergeFieldDefinition]: ...

    @abstractmethod
    async def resolve(self, entity_id: int, db: AsyncSession) -> dict: ...


def format_indirizzo(indirizzo: Indirizzo | None) -> str | None:
    """Compone un indirizzo su una riga: ``via, civico, cap comune (prov)``."""
    if indirizzo is None:
        return None

    via = indirizzo.prima_riga or ""
    if indirizzo.numero_civico:
        via = f"{via}, {indirizzo.numero_civico}" if via else indirizzo.numero_civico

    comune = indirizzo.comune
    localita = " ".join(
        p for p in [indirizzo.cap, comune.descrizione if comune else None] if p
    )

    return ", ".join(p for p in [via, localita] if p) or None
