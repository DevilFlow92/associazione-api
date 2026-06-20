from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.utente import Utente
    from app.models.voce_contabilita import VoceContabilita


class ConfigurazioneBandaAnno(Base):
    __tablename__ = "configurazioni_banda_anno"

    id: Mapped[int] = mapped_column(primary_key=True)
    banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bande.codice"), nullable=False
    )
    anno: Mapped[int] = mapped_column(Integer, nullable=False)
    quota_annuale_attesa: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    saldo_iniziale_cassa: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    saldo_iniziale_banca: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    voce_contabilita_quote_id: Mapped[int | None] = mapped_column(
        ForeignKey("voci_contabilita.id"), nullable=True
    )
    chiuso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_chiusura: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    chiuso_da_utente_id: Mapped[int | None] = mapped_column(
        ForeignKey("utenti.id"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("banda_codice", "anno", name="uq_configurazione_banda_anno"),
    )

    voce_contabilita_quote: Mapped[VoceContabilita | None] = relationship(
        foreign_keys=[voce_contabilita_quote_id]
    )
    chiuso_da_utente: Mapped[Utente | None] = relationship(
        foreign_keys=[chiuso_da_utente_id]
    )
