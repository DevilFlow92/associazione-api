from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.socio import Socio


class Iscrizione(Base):
    """Adesione annuale di un socio.

    Ogni socio si iscrive ogni anno: la prima iscrizione è derivabile come
    l'anno minimo per socio, le successive sono rinnovi. Porta la quota di
    partecipazione con il relativo stato, e referenzia il documento di adesione
    e la ricevuta emessa per il pagamento della quota.
    """

    __tablename__ = "iscrizioni"
    __table_args__ = (
        UniqueConstraint("socio_id", "anno", name="uq_iscrizione_socio_anno"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    socio_id: Mapped[int] = mapped_column(ForeignKey("soci.id"), nullable=False)
    anno: Mapped[int] = mapped_column(Integer, nullable=False)
    quota_partecipazione: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stato_iscrizione_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("stati_iscrizione.codice"), nullable=False
    )
    documento_id: Mapped[int | None] = mapped_column(
        ForeignKey("documenti.id"), nullable=True
    )
    ricevuta_id: Mapped[int | None] = mapped_column(
        ForeignKey("ricevute.id"), nullable=True
    )
    data_iscrizione: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    socio: Mapped[Socio] = relationship(back_populates="iscrizioni")
