from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.nome_parte import NomeParte
    from app.models.servizio import Servizio


class RepertorioItem(Base):
    """Brano (NomeParte) inserito nel programma di un Servizio, con ordine.

    ``servizio_id`` è nullable in previsione delle fasi successive del
    backlog Attività (``prova_id``), ma per ora è sempre valorizzato: il
    CHECK lo impone finché quella fase non arriva.
    """

    __tablename__ = "voci_repertorio"
    __table_args__ = (
        UniqueConstraint(
            "nome_parte_id",
            "servizio_id",
            name="uq_repertorio_item_nome_parte_servizio",
        ),
        CheckConstraint(
            "servizio_id IS NOT NULL", name="ck_repertorio_item_servizio_id_required"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_parte_id: Mapped[int] = mapped_column(
        ForeignKey("nome_parti.id"), nullable=False
    )
    servizio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servizi.id"), nullable=True
    )
    ordine: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    nome_parte: Mapped[NomeParte] = relationship(foreign_keys=[nome_parte_id])
    servizio: Mapped[Servizio | None] = relationship(foreign_keys=[servizio_id])
