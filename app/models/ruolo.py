from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.relations import ruoli_permessi, utenti_ruoli

if TYPE_CHECKING:
    from app.models.permesso import Permesso
    from app.models.utente import Utente


class Ruolo(Base):
    """Ruolo configurabile per associazione.

    Raggruppa un insieme di permessi. Tipicamente mappa una carica del
    direttivo (presidente, tesoriere, segretario, ...) oppure un profilo
    macchina (worker, importer). Lo stesso nome di ruolo può esistere per
    bande diverse, perciò l'unicità è su ``(banda_codice, nome)``; ruoli a
    ``banda_codice`` nullo sono globali (es. superuser).
    """

    __tablename__ = "ruoli"
    __table_args__ = (
        UniqueConstraint("banda_codice", "nome", name="uq_ruolo_banda_nome"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(64))
    descrizione: Mapped[str | None] = mapped_column(String(255), nullable=True)
    banda_codice: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    permessi: Mapped[list[Permesso]] = relationship(
        secondary=ruoli_permessi, lazy="selectin"
    )
    utenti: Mapped[list[Utente]] = relationship(
        secondary=utenti_ruoli, back_populates="ruoli"
    )
