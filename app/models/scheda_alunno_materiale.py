from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.scheda_alunno import SchedaAlunno


class SchedaAlunnoMateriale(Base):
    """Materiale didattico allegato a una scheda alunno: un file caricato su
    storage oppure un link esterno, mai entrambi — arco esclusivo imposto dal
    CHECK ``ck_scheda_alunno_materiale_arc_storage_key_url`` nella migration,
    stesso pattern già in uso per l'arco di ``Presenza``
    (``app.models.presenza``).

    ``nome_file_originale``/``mime_type``/``dimensione_bytes`` sono valorizzati
    solo per i materiali di tipo file: servono al download (nome file
    proposto) e sono informativi, non validati contro il contenuto.

    Nessuno storico a differenza di ``SchedaAlunnoVoce``: la cancellazione è
    un hard delete, vedi ``SchedaAlunnoMaterialeService.delete``.

    ``caricato_da_persona_id`` è lo stesso pattern audit di
    ``SchedaAlunno.aggiornato_da_persona_id``: valorizzato dal service con la
    Persona dell'utente autenticato, mai dal payload.
    """

    __tablename__ = "scheda_alunno_materiali"
    __table_args__ = (
        CheckConstraint(
            "(storage_key IS NOT NULL AND url IS NULL) OR "
            "(storage_key IS NULL AND url IS NOT NULL)",
            name="ck_scheda_alunno_materiale_arc_storage_key_url",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    scheda_alunno_id: Mapped[int] = mapped_column(
        ForeignKey("schede_alunno.id"), nullable=False
    )
    titolo: Mapped[str] = mapped_column(String(200), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    nome_file_originale: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dimensione_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    caricato_da_persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("persone.id"), nullable=True
    )
    data_caricamento: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    scheda_alunno: Mapped[SchedaAlunno] = relationship(
        "SchedaAlunno", foreign_keys=[scheda_alunno_id], back_populates="materiali"
    )
