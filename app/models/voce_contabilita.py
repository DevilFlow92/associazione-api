from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.flusso_cassa import FlussoCassa
    from app.models.lookups import (
        SezioneRendiconto,
        SottovoceRendiconto,
        VoceRendiconto,
    )


class VoceContabilita(Base):
    __tablename__ = "voci_contabilita"

    id: Mapped[int] = mapped_column(primary_key=True)
    banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bande.codice"), nullable=False
    )
    voce_contabilita: Mapped[str] = mapped_column(String(100))
    sezione_rendiconto_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sezioni_rendiconto.codice"), nullable=False
    )
    voce_rendiconto_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("voci_rendiconto.codice"), nullable=False
    )
    sottovoce_rendiconto_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sottovoci_rendiconto.codice"), nullable=False
    )

    # ``lazy="selectin"`` carica le tre lookup insieme alla voce in ogni query
    # (anche quando la voce è annidata, es. voce_contabilita_quote nella
    # configurazione), evitando lazy-load in contesto async durante la
    # serializzazione.
    sezione_rendiconto: Mapped[SezioneRendiconto] = relationship(
        "SezioneRendiconto", foreign_keys=[sezione_rendiconto_codice], lazy="selectin"
    )
    voce_rendiconto: Mapped[VoceRendiconto] = relationship(
        "VoceRendiconto", foreign_keys=[voce_rendiconto_codice], lazy="selectin"
    )
    sottovoce_rendiconto: Mapped[SottovoceRendiconto] = relationship(
        "SottovoceRendiconto",
        foreign_keys=[sottovoce_rendiconto_codice],
        lazy="selectin",
    )

    flussi: Mapped[list[FlussoCassa]] = relationship(back_populates="voce_contabilita")
