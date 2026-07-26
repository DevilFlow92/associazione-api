from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.nome_parte import NomeParte
    from app.models.prova import Prova
    from app.models.servizio import Servizio


class RepertorioItem(Base):
    """Brano (NomeParte) inserito nel programma di un Servizio o di una Prova.

    ``servizio_id`` e ``prova_id`` formano un arc esclusivo: esattamente uno
    dei due deve essere valorizzato. Il CHECK è espresso con AND/OR anziché
    con un cast a intero per restare portabile tra PostgreSQL (produzione) e
    SQLite (test).
    """

    __tablename__ = "voci_repertorio"
    __table_args__ = (
        UniqueConstraint(
            "nome_parte_id",
            "servizio_id",
            name="uq_repertorio_item_nome_parte_servizio",
        ),
        UniqueConstraint(
            "nome_parte_id",
            "prova_id",
            name="uq_repertorio_item_nome_parte_prova",
        ),
        CheckConstraint(
            "(servizio_id IS NOT NULL AND prova_id IS NULL) OR "
            "(servizio_id IS NULL AND prova_id IS NOT NULL)",
            name="ck_repertorio_item_arc_servizio_prova",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_parte_id: Mapped[int] = mapped_column(
        ForeignKey("nome_parti.id"), nullable=False
    )
    servizio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servizi.id"), nullable=True
    )
    prova_id: Mapped[int | None] = mapped_column(ForeignKey("prove.id"), nullable=True)
    ordine: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    nome_parte: Mapped[NomeParte] = relationship(foreign_keys=[nome_parte_id])
    servizio: Mapped[Servizio | None] = relationship(foreign_keys=[servizio_id])
    prova: Mapped[Prova | None] = relationship(foreign_keys=[prova_id])
