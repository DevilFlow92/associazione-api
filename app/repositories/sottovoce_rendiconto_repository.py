from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lookups import SottovoceRendiconto
from app.models.relations import voci_sottovoci_rendiconto
from app.repositories.lookup import LookupRepository


class SottovoceRendicontoRepository(LookupRepository[SottovoceRendiconto]):
    """Lookup repository per le sottovoci con filtro ``voce_codice``.

    Il legame voce↔sottovoce è molti-a-molti (tabella ponte
    ``voci_sottovoci_rendiconto``), quindi il filtro non è una semplice colonna
    sul modello e va risolto con un JOIN sulla tabella ponte. Gli altri filtri
    ricadono sul comportamento generico di :class:`LookupRepository`.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, SottovoceRendiconto)

    def _apply_filters(self, stmt, filters: dict[str, Any] | None):
        filters = dict(filters or {})
        voce_codice = filters.pop("voce_codice", None)
        if voce_codice is not None:
            stmt = stmt.join(
                voci_sottovoci_rendiconto,
                voci_sottovoci_rendiconto.c.sottovoce_codice
                == SottovoceRendiconto.codice,
            ).where(voci_sottovoci_rendiconto.c.voce_codice == voce_codice)
        return super()._apply_filters(stmt, filters)
