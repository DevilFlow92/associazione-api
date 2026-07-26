from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.persona import Persona
    from app.models.prova import Prova
    from app.models.servizio import Servizio


class StatoPresenza(enum.StrEnum):
    PRESENTE = "PRESENTE"
    ASSENTE = "ASSENTE"
    GIUSTIFICATO = "GIUSTIFICATO"


class Presenza(Base):
    """Organico e presenza effettiva di una persona a un servizio o a una prova.

    ``stato`` è nullo finché la persona è solo "in organico" e non è ancora
    stata tracciata la presenza effettiva. ``servizio_id`` e ``prova_id``
    formano un arc esclusivo: esattamente uno dei due deve essere valorizzato
    (una Presenza appartiene o a un Servizio o a una Prova, mai a entrambi né
    a nessuno). Il CHECK è espresso con AND/OR anziché con un cast a intero
    per restare portabile tra PostgreSQL (produzione) e SQLite (test).
    """

    __tablename__ = "presenze"
    __table_args__ = (
        UniqueConstraint(
            "persona_id", "servizio_id", name="uq_presenza_persona_servizio"
        ),
        UniqueConstraint("persona_id", "prova_id", name="uq_presenza_persona_prova"),
        CheckConstraint(
            "(servizio_id IS NOT NULL AND prova_id IS NULL) OR "
            "(servizio_id IS NULL AND prova_id IS NOT NULL)",
            name="ck_presenza_arc_servizio_prova",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("persone.id"), nullable=False)
    servizio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servizi.id"), nullable=True
    )
    prova_id: Mapped[int | None] = mapped_column(ForeignKey("prove.id"), nullable=True)
    stato: Mapped[StatoPresenza | None] = mapped_column(
        Enum(StatoPresenza, name="stato_presenza"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    persona: Mapped[Persona] = relationship(foreign_keys=[persona_id])
    servizio: Mapped[Servizio | None] = relationship(foreign_keys=[servizio_id])
    prova: Mapped[Prova | None] = relationship(foreign_keys=[prova_id])
