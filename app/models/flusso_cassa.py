from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.voce_contabilita import VoceContabilita


class FlussoCassa(Base):
    __tablename__ = "flussi_cassa"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_registrazione: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    descrizione_operazione: Mapped[str] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    voce_contabilita_id: Mapped[int] = mapped_column(
        ForeignKey("voci_contabilita.id"), nullable=False
    )
    importo: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    segno: Mapped[str] = mapped_column(String(5))
    natura_flusso_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("nature_flusso.codice"), nullable=False
    )

    voce_contabilita: Mapped[VoceContabilita] = relationship(back_populates="flussi")
