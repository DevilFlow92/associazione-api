from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flusso_cassa import FlussoCassa
from app.models.lookups import (
    NaturaFlusso,
    SezioneRendiconto,
    SottovoceRendiconto,
    VoceRendiconto,
)
from app.models.relations import voci_sottovoci_rendiconto
from app.models.voce_contabilita import VoceContabilita
from app.schemas.flusso_cassa import FlussoCassaCreate, FlussoCassaUpdate


class FlussoCassaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, offset: int = 0, limit: int = 20) -> list[FlussoCassa]:
        stmt = select(FlussoCassa).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(FlussoCassa)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, flusso_id: int) -> FlussoCassa | None:
        stmt = select(FlussoCassa).where(FlussoCassa.id == flusso_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_iscrizione_id(self, iscrizione_id: int) -> FlussoCassa | None:
        stmt = select(FlussoCassa).where(FlussoCassa.iscrizione_id == iscrizione_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_other_leg_by_trasferimento_id(
        self, trasferimento_id: UUID, exclude_id: int
    ) -> FlussoCassa | None:
        """Restituisce l'altra gamba di un trasferimento (stesso UUID, id diverso)."""
        stmt = select(FlussoCassa).where(
            FlussoCassa.trasferimento_id == trasferimento_id,
            FlussoCassa.id != exclude_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_voce(
        self, voce_contabilita_id: int, offset: int = 0, limit: int = 20
    ) -> list[FlussoCassa]:
        stmt = (
            select(FlussoCassa)
            .where(FlussoCassa.voce_contabilita_id == voce_contabilita_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_voce(self, voce_contabilita_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(FlussoCassa)
            .where(FlussoCassa.voce_contabilita_id == voce_contabilita_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, data: FlussoCassaCreate) -> FlussoCassa:
        flusso = FlussoCassa(**data.model_dump())
        self.db.add(flusso)
        await self.db.commit()
        await self.db.refresh(flusso)
        return flusso

    async def update(self, flusso: FlussoCassa, data: FlussoCassaUpdate) -> FlussoCassa:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(flusso, field, value)
        await self.db.commit()
        await self.db.refresh(flusso)
        return flusso

    async def delete(self, flusso: FlussoCassa) -> None:
        await self.db.delete(flusso)
        await self.db.commit()

    # ── Operazioni transazionali (commit gestito dal service) ────────────────
    def add_no_commit(self, flusso: FlussoCassa) -> None:
        """Accoda un insert senza fare commit (per inserimenti atomici a coppie)."""
        self.db.add(flusso)

    def update_no_commit(self, flusso: FlussoCassa, **fields) -> None:
        """Applica aggiornamenti di campo senza fare commit."""
        for field, value in fields.items():
            setattr(flusso, field, value)

    async def delete_no_commit(self, flusso: FlussoCassa) -> None:
        """Accoda una delete senza fare commit (per cancellazioni atomiche)."""
        await self.db.delete(flusso)

    async def commit(self) -> None:
        await self.db.commit()

    async def refresh(self, flusso: FlussoCassa) -> None:
        await self.db.refresh(flusso)

    # ── Rendiconto structure & aggregation ───────────────────────────────────

    async def get_struttura_rendiconto(
        self,
    ) -> list[tuple[int, str, int, str, int, str]]:
        """Full Modello D skeleton: one row per (sezione, voce, sottovoce)."""
        stmt = (
            select(
                SezioneRendiconto.codice,
                SezioneRendiconto.descrizione,
                VoceRendiconto.codice,
                VoceRendiconto.descrizione,
                SottovoceRendiconto.codice,
                SottovoceRendiconto.descrizione,
            )
            .join(
                VoceRendiconto,
                VoceRendiconto.sezione_codice == SezioneRendiconto.codice,
            )
            .join(
                voci_sottovoci_rendiconto,
                voci_sottovoci_rendiconto.c.voce_codice == VoceRendiconto.codice,
            )
            .join(
                SottovoceRendiconto,
                SottovoceRendiconto.codice
                == voci_sottovoci_rendiconto.c.sottovoce_codice,
            )
            .order_by(
                SezioneRendiconto.codice,
                VoceRendiconto.codice,
                SottovoceRendiconto.codice,
            )
        )
        result = await self.db.execute(stmt)
        rows: list[tuple[int, str, int, str, int, str]] = []
        for sez_cod, sez_desc, voce_cod, voce_desc, sv_cod, sv_desc in result:
            rows.append((sez_cod, sez_desc, voce_cod, voce_desc, sv_cod, sv_desc))
        return rows

    # ── Rendiconto aggregation ────────────────────────────────────────────────

    async def get_aggregati_per_rendiconto(
        self, banda_codice: int, anno: int
    ) -> list[tuple[int, int, int, Decimal]]:
        """One row per flusso:
        (sezione_cod, voce_cod, sottovoce_cod, importo_signed)."""
        stmt = (
            select(
                VoceContabilita.sezione_rendiconto_codice,
                VoceContabilita.voce_rendiconto_codice,
                VoceContabilita.sottovoce_rendiconto_codice,
                FlussoCassa.importo,
                FlussoCassa.segno,
            )
            .join(
                VoceContabilita, FlussoCassa.voce_contabilita_id == VoceContabilita.id
            )
            .where(
                VoceContabilita.banda_codice == banda_codice,
                extract("year", FlussoCassa.data_registrazione) == anno,
            )
        )
        result = await self.db.execute(stmt)
        rows: list[tuple[int, int, int, Decimal]] = []
        for sez_cod, voce_cod, sv_cod, importo, segno in result:
            if importo is not None:
                amount = Decimal(str(importo))
                rows.append(
                    (sez_cod, voce_cod, sv_cod, amount if segno == "+" else -amount)
                )
        return rows

    async def get_aggregati_mensili(
        self, banda_codice: int, anno: int
    ) -> list[tuple[int, int, Decimal]]:
        """One row per flusso: (mese, sezione_rendiconto_codice, importo_signed)."""
        stmt = (
            select(
                extract("month", FlussoCassa.data_registrazione),
                VoceContabilita.sezione_rendiconto_codice,
                FlussoCassa.importo,
                FlussoCassa.segno,
            )
            .join(
                VoceContabilita, FlussoCassa.voce_contabilita_id == VoceContabilita.id
            )
            .where(
                VoceContabilita.banda_codice == banda_codice,
                extract("year", FlussoCassa.data_registrazione) == anno,
            )
        )
        result = await self.db.execute(stmt)
        rows: list[tuple[int, int, Decimal]] = []
        for mese, sez_cod, importo, segno in result:
            if importo is not None:
                amount = Decimal(str(importo))
                rows.append((int(mese), sez_cod, amount if segno == "+" else -amount))
        return rows

    async def get_aggregati_per_natura(
        self, banda_codice: int, anno: int
    ) -> dict[str, Decimal]:
        """Returns {natura_descrizione.lower():
        signed_sum} for saldo_finale computation."""
        stmt = (
            select(
                NaturaFlusso.descrizione,
                FlussoCassa.importo,
                FlussoCassa.segno,
            )
            .join(
                VoceContabilita, FlussoCassa.voce_contabilita_id == VoceContabilita.id
            )
            .join(NaturaFlusso, FlussoCassa.natura_flusso_codice == NaturaFlusso.codice)
            .where(
                VoceContabilita.banda_codice == banda_codice,
                extract("year", FlussoCassa.data_registrazione) == anno,
            )
        )
        result = await self.db.execute(stmt)
        natura_dict: dict[str, Decimal] = {}
        for descrizione, importo, segno in result:
            if importo is not None:
                key = descrizione.lower()
                amount = Decimal(str(importo))
                signed = amount if segno == "+" else -amount
                natura_dict[key] = natura_dict.get(key, Decimal(0)) + signed
        return natura_dict
