from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.scheda_alunno import SchedaAlunno


class SchedaAlunnoAutovalutazione(Base):
    """Diario di autovalutazione scritto dall'alunno stesso sulla propria
    scheda: annotazioni libere sui propri progressi, non un giudizio
    dell'insegnante.

    PRIMO caso nel progetto di scrittura concessa all'alunno sulla propria
    scheda: ``SchedaAlunnoVoce`` e ``SchedaAlunnoMateriale`` sono scritti solo
    da insegnante/coordinatore (``assert_puo_scrivere_scheda``); qui vale
    l'esatto opposto, un perimetro row-level dedicato e deliberatamente NON
    derivato da quella funzione — vedi
    ``assert_puo_scrivere_autovalutazione`` in
    ``app/services/rbac_row_level.py``.

    ``persona_id`` è l'autore, sempre l'alunno titolare della scheda:
    valorizzato dal service dalla Persona collegata all'utente autenticato,
    mai dal payload — stesso principio di
    ``SchedaAlunno.aggiornato_da_persona_id``.

    ``data_modifica`` resta nulla finché la voce non viene editata dopo la
    creazione, per distinguere "creata il" da "modificata l'ultima volta il"
    nella UI.
    """

    __tablename__ = "scheda_alunno_autovalutazioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheda_alunno_id: Mapped[int] = mapped_column(
        ForeignKey("schede_alunno.id"), nullable=False
    )
    persona_id: Mapped[int] = mapped_column(ForeignKey("persone.id"), nullable=False)
    testo: Mapped[str] = mapped_column(String(1000), nullable=False)
    data_creazione: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    data_modifica: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    scheda_alunno: Mapped[SchedaAlunno] = relationship(
        "SchedaAlunno",
        foreign_keys=[scheda_alunno_id],
        back_populates="autovalutazioni",
    )
