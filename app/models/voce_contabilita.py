from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.flusso_cassa import FlussoCassa


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

    flussi: Mapped[list[FlussoCassa]] = relationship(back_populates="voce_contabilita")
