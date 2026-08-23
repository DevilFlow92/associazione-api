from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.scheda_alunno_voce import StatoVoceProgramma

if TYPE_CHECKING:
    from app.models.persona import Persona
    from app.models.scheda_alunno_voce import SchedaAlunnoVoce


class SchedaAlunnoVoceStorico(Base):
    """Storico append-only dei cambi di stato delle voci di programma.

    ``scheda_alunno_id`` e ``voce_catalogo_id`` sono denormalizzati di
    proposito (``Integer`` semplice, non FK): la voce (``SchedaAlunnoVoce``)
    a cui la riga si riferisce può essere cancellata — ``scheda_alunno_voce_id``
    diventa NULL (``ON DELETE SET NULL``) ma lo storico deve restare
    interrogabile per scheda e per voce di catalogo senza dipendere da una
    riga che potrebbe non esistere più.

    Nessuna UPDATE né DELETE previste su questa tabella al di fuori
    dell'azzeramento di ``scheda_alunno_voce_id`` alla cancellazione della
    voce: è un log, non uno stato mutabile.
    """

    __tablename__ = "scheda_alunno_voci_storico"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheda_alunno_voce_id: Mapped[int | None] = mapped_column(
        ForeignKey("scheda_alunno_voci.id", ondelete="SET NULL"), nullable=True
    )
    scheda_alunno_id: Mapped[int] = mapped_column(Integer, nullable=False)
    voce_catalogo_id: Mapped[int] = mapped_column(Integer, nullable=False)
    stato_precedente: Mapped[StatoVoceProgramma | None] = mapped_column(
        Enum(StatoVoceProgramma, name="stato_voce_programma"), nullable=True
    )
    stato_nuovo: Mapped[StatoVoceProgramma] = mapped_column(
        Enum(StatoVoceProgramma, name="stato_voce_programma"), nullable=False
    )
    modificato_da_persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("persone.id"), nullable=True
    )
    data_modifica: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    scheda_alunno_voce: Mapped[SchedaAlunnoVoce | None] = relationship(
        "SchedaAlunnoVoce", foreign_keys=[scheda_alunno_voce_id]
    )
    modificato_da: Mapped[Persona | None] = relationship(
        "Persona", foreign_keys=[modificato_da_persona_id]
    )
